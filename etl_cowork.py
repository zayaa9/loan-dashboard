"""
etl_cowork.py — Cowork автоматжуулалтын ETL script
=====================================================
Үүрэг:
  1. overdue_*.csv + features_*.csv файлуудыг олно
  2. user_id-оор LEFT JOIN хийнэ
  3. Давхардсан баганыг цэвэрлэнэ
  4. preprocess() логикийг ажиллуулна
  5. archive/ folder-д YYYYMM.parquet хэлбэрээр хадгална

Ажиллуулах:
  python etl_cowork.py
  python etl_cowork.py --overdue /path/to/overdue.csv --features /path/to/features.csv
  python etl_cowork.py --period 2026-05               # огноог гараас тохируулах
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ── Тохиргоо ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent          # script-тэй ижил хавтас
DATA_DIR    = BASE_DIR / "data"              # CSV файлуудын хавтас
ARCHIVE_DIR = BASE_DIR / "archive"          # Streamlit-ийн archive/ хавтас
LOG_FILE    = BASE_DIR / "etl.log"

# Файлын нэрийн glob pattern — өөрийн нэрлэлтэд тохируулах
OVERDUE_GLOB  = "overdue*.csv"
FEATURES_GLOB = "features*.csv"

# Merge key
JOIN_KEY = "user_id"

# overdue-д байх боловч features-т давхардсан → drop хийх баганууд
FEATURES_DROP_COLS = ["status", "created_at"]

# Bucket тохиргоо (config.py-тай ижил)
BUCKET_BINS = [-1, 0, 1, 5, 10, 15, 30, 9999]
BUCKET_LBLS = ["0", "1", "2–5", "6–10", "11–15", "16–30", "30+"]


# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("etl")


# ── 1. Файл олох ──────────────────────────────────────────────────────────────
def find_latest_file(folder: Path, pattern: str) -> Path:
    """
    Тухайн pattern-д тохирох хамгийн сүүлийн файлыг буцаана.
    Нэг ч файл олдохгүй бол алдаа гаргана.
    """
    files = sorted(folder.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(
            f"'{pattern}' pattern-д тохирох файл '{folder}' хавтасд олдсонгүй.\n"
            f"Файлын нэрийн жишээ: overdue_20260519.csv"
        )
    log.info(f"Олдсон файл: {files[0].name}  ({len(files)} нийт)")
    return files[0]


# ── 2. CSV унших ──────────────────────────────────────────────────────────────
def read_csv(path: Path, label: str) -> pd.DataFrame:
    """CSV уншиж, баганын нэрийг жижиг үсгээр нормчилно.

    acnt_no мэт урт ID баганыг ТЕКСТЭЭР уншина — эс бөгөөс pandas том тоог
    float болгож хувиргаад нарийвчлалаа алдаж бүх дугаар ижил болдог.
    (dtype dict-д байхгүй баганыг pandas үл тоомсорлоно тул бүх хувилбарыг бичсэн.)
    """
    log.info(f"{label} уншиж байна: {path.name}")
    id_as_str = {c: str for c in ("acnt_no", "ACNT_NO", "Acnt_No", "acnt_No")}
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False, dtype=id_as_str)
    df.columns = df.columns.str.strip().str.lower()
    log.info(f"  → {len(df):,} мөр · {len(df.columns)} багана")
    return df


# ── 3. Merge ──────────────────────────────────────────────────────────────────
def merge_dataframes(df_overdue: pd.DataFrame, df_features: pd.DataFrame) -> pd.DataFrame:
    """
    overdue + features-ийг user_id-оор LEFT JOIN хийнэ.
    - overdue-д байгаа бүх зээлийн данс хадгалагдана
    - features-д байхгүй 112 харилцагч NaN-тай орно
    """
    # features-ийн давхардсан баганыг урьдчилж устгана
    drop_cols = [c for c in FEATURES_DROP_COLS if c in df_features.columns]
    if drop_cols:
        log.info(f"features-ээс давхардсан баганыг устгана: {drop_cols}")
        df_features = df_features.drop(columns=drop_cols)

    # features-ийг user_id-аар ЦОР ГАНЦ болгоно.
    # Эс бөгөөс давхардсан user_id нь LEFT JOIN-д overdue мөрийг үржүүлж,
    # зээлийн дансны тоог хөөрөгдөнө (ж: 31,667 → 35,469).
    dup_n = int(df_features[JOIN_KEY].duplicated().sum())
    if dup_n:
        log.info(f"features-д {dup_n:,} давхардсан user_id олдлоо — цор ганц болгоно (нэг мөр үлдээнэ)")
        df_features = df_features.drop_duplicates(subset=JOIN_KEY, keep="first")

    before = len(df_overdue)
    df = df_overdue.merge(df_features, on=JOIN_KEY, how="left")
    after  = len(df)

    matched   = df[JOIN_KEY].isin(df_features[JOIN_KEY]).sum()
    unmatched = before - matched
    log.info(
        f"Merge дууслаа: {after:,} мөр  |  "
        f"Тохирсон: {matched:,}  |  "
        f"features-гүй: {unmatched:,}"
    )

    # total_score давхардал шийдэх
    # overdue-д total_score, features-д total_score_calc байна
    # → total_score (overdue-ийн) хадгалж, total_score_calc-ийг устгана
    if "total_score_calc" in df.columns:
        log.info("total_score_calc баганыг устгана (total_score байгаа учраас)")
        df = df.drop(columns=["total_score_calc"])

    return df


# ── 4. Preprocess ─────────────────────────────────────────────────────────────
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    preprocess.py-тай ижил логик — Streamlit-д @st.cache_data ашигладаг тул
    ETL-д тусдаа хуулбар болгон хэрэгжүүлсэн.
    """
    df = df.copy()

    # ── Огноо ────────────────────────────────────────────────────────────────
    if "adv_date" in df.columns:
        df["adv_date"] = pd.to_datetime(df["adv_date"], errors="coerce")

    # ── Тоон баганууд ─────────────────────────────────────────────────────────
    num_cols = ["adv_amt", "total_score", "max_overdue_day", "max_active_overdue_day", "calc_lmt"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "max_active_overdue_day" in df.columns:
        df["max_active_overdue_day"] = df["max_active_overdue_day"].fillna(0)

    # ── Цалингийн -1 → NaN ───────────────────────────────────────────────────
    salary_cols = [
        "slry_last_amt", "slry_last_avg_6m", "slry_last_row_cnt_24m",
        "zms_monthly_payment", "zms_closed_ln_total_amount",
    ]
    for c in salary_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace(-1, np.nan)

    # ── Boolean хөрвүүлэлт ────────────────────────────────────────────────────
    def _to_bool(x):
        if isinstance(x, (bool, np.bool_)):
            return bool(x)
        if isinstance(x, (int, float, np.integer, np.floating)):
            if pd.isna(x):
                return np.nan
            if x == 1: return True
            if x == 0: return False
            return np.nan
        s = str(x).strip().upper()
        if s in ("TRUE", "1", "1.0", "YES", "Y", "T"):  return True
        if s in ("FALSE", "0", "0.0", "NO", "N", "F"):  return False
        return np.nan

    for c in ["is_overdue", "active_overdue"]:
        if c in df.columns:
            df[c] = df[c].map(_to_bool)

    if "status_1" in df.columns:
        df["status_1"] = df["status_1"].astype(str).str.strip().replace("N", "C")

    # ── Bucket ────────────────────────────────────────────────────────────────
    if "max_active_overdue_day" in df.columns:
        df["bucket"] = pd.cut(
            df["max_active_overdue_day"].fillna(0),
            bins=BUCKET_BINS, labels=BUCKET_LBLS, right=True,
        )

    # ── Огноогийн derived баганууд ────────────────────────────────────────────
    if "adv_date" in df.columns:
        df["loan_ym"]   = df["adv_date"].dt.to_period("M").astype(str)
        df["loan_year"] = df["adv_date"].dt.year

    # ── Score band ────────────────────────────────────────────────────────────
    if "total_score" in df.columns:
        df["score_band"] = pd.cut(
            df["total_score"],
            bins=[0, 350, 400, 450, 500, 550, 9999],
            labels=["<350", "351–400", "401–450", "451–500", "501–550", "551+"],
            right=True,
        )

    # ── Насны бүлэг ───────────────────────────────────────────────────────────
    if "age" in df.columns:
        df["age_group"] = pd.cut(
            pd.to_numeric(df["age"], errors="coerce"),
            bins=[0, 17, 18, 20, 25, 30, 35, 40, 99],
            labels=["17-оос бага", "18", "19–20", "21–25", "26–30", "31–35", "36–40", "40+"],
            right=True,
        )

    # ── Цалингийн тасралтгүй байдал ───────────────────────────────────────────
    if "slry_has_cont_salary_3m" in df.columns:
        df["slry_cont_label"] = (
            pd.to_numeric(df["slry_has_cont_salary_3m"], errors="coerce")
            .map({1: "Тасралтгүй 3 сар", 0: "Тасралттай"})
            .fillna("Мэдээлэл байхгүй")
        )

    # ── Boolean label баганууд ────────────────────────────────────────────────
    bool_maps = {
        "gender":             ("gender_label",  {True: "Эрэгтэй",  False: "Эмэгтэй"}),
        "has_ios":            ("ios_label",     {True: "iOS",      False: "Android"}),
        "is_bio_login":       ("bio_label",     {True: "Биометр",  False: "Нууц үг"}),
        "is_device_remember": ("dev_label",     {True: "Санасан",  False: "Санаагүй"}),
    }
    for src, (tgt, mp) in bool_maps.items():
        if src in df.columns:
            df[src] = df[src].map(_to_bool)
            df[tgt] = df[src].map(mp)

    # ── Гэрлэлтийн байдал ────────────────────────────────────────────────────
    if "marital_status" in df.columns:
        df["marital_label"] = df["marital_status"].map(
            {"SNG": "Ганц бие", "MRD": "Гэрлэсэн",
             "BGF": "Хамтран амьд.", "DIV": "Салсан", "WID": "Бэлэвсэн"}
        ).fillna("Тодорхойгүй")

    # ── Байршлын төрөл ────────────────────────────────────────────────────────
    if "location" in df.columns:
        df["location_type"] = df["location"].apply(
            lambda x: "Улаанбаатар" if "УЛААНБААТАР" in str(x).upper() else "Орон нутаг"
        )

    # ── cust_code alias (Streamlit COL_CUST = "cust_code" хүлээнэ) ───────────
    # user_id → cust_code нэрийг нэмэх (хуулбар биш, alias)
    if "user_id" in df.columns and "cust_code" not in df.columns:
        df["cust_code"] = df["user_id"]

    log.info(f"Preprocess дууслаа: {len(df):,} мөр · {len(df.columns)} bagana")
    return df


# ── 5. Archive-д хадгалах ─────────────────────────────────────────────────────
def save_to_archive(df: pd.DataFrame, period: str, source_files: dict) -> Path:
    """
    DataFrame-ийг archive/YYYYMM.parquet хэлбэрээр хадгална.
    Streamlit-ийн archive.py-тай бүрэн нийцтэй.
    """
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = ARCHIVE_DIR / f"{period}.parquet"
    meta_path    = ARCHIVE_DIR / f"{period}.json"

    # Categorical dtype-ийг string болгох — parquet нийцтэй байх
    for col in df.select_dtypes(["category"]).columns:
        df[col] = df[col].astype(str)

    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    meta = {
        "filename":     f"overdue+features merge — {period}",
        "saved_at":     datetime.now().isoformat(),
        "rows":         len(df),
        "columns":      len(df.columns),
        "source_files": source_files,
        "etl_version":  "1.0",
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    log.info(f"Хадгаллаа: {parquet_path.name}  ({len(df):,} мөр · {parquet_path.stat().st_size // 1024} KB)")
    return parquet_path


# ── 6. Шалгалт (sanity check) ─────────────────────────────────────────────────
def sanity_check(df: pd.DataFrame) -> None:
    """Хадгалахаас өмнө чухал баганыг шалгана."""
    required = ["status_1", "max_active_overdue_day", "cust_code"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        log.warning(f"Дутуу чухал баганууд: {missing}")
    else:
        log.info("Sanity check: бүх чухал багана байна")

    # Хоосон байдал
    key_cols = ["status_1", "max_active_overdue_day", "adv_amt"]
    for c in key_cols:
        if c in df.columns:
            null_pct = df[c].isna().mean() * 100
            if null_pct > 10:
                log.warning(f"  {c}: {null_pct:.1f}% хоосон — шалгана уу")
            else:
                log.info(f"  {c}: {null_pct:.1f}% хоосон — OK")


# ── Үндсэн функц ──────────────────────────────────────────────────────────────
def run(overdue_path: Path, features_path: Path, period: str) -> None:
    log.info("=" * 60)
    log.info(f"ETL эхэллээ — үе: {period}")
    log.info("=" * 60)

    # 1. Унших
    df_ov = read_csv(overdue_path,  "overdue")
    df_ft = read_csv(features_path, "features")

    # 2. Merge
    df = merge_dataframes(df_ov, df_ft)

    # 3. Preprocess
    df = preprocess(df)

    # 4. Шалгалт
    sanity_check(df)

    # 5. Хадгалах
    save_to_archive(df, period, {
        "overdue":  overdue_path.name,
        "features": features_path.name,
    })

    log.info(f"ETL амжилттай дууслаа — {period}")
    log.info("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Overdue ETL — Cowork runner")
    parser.add_argument("--overdue",  type=Path, help="overdue CSV файлын зам")
    parser.add_argument("--features", type=Path, help="features CSV файлын зам")
    parser.add_argument(
        "--period",
        default=datetime.today().strftime("%Y-%m-%d"),
        help="Архивын нэр, жишээ: 2026-05-19 (default: өнөөдрийн огноо)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help=f"CSV байрлах хавтас (default: {DATA_DIR})",
    )
    args = parser.parse_args()

    # Файлын зам тогтоох
    data_dir = args.data_dir
    try:
        overdue_path  = args.overdue  or find_latest_file(data_dir, OVERDUE_GLOB)
        features_path = args.features or find_latest_file(data_dir, FEATURES_GLOB)
    except FileNotFoundError as e:
        log.error(str(e))
        sys.exit(1)

    try:
        run(overdue_path, features_path, args.period)
    except Exception as e:
        log.exception(f"ETL алдаа гарлаа: {e}")
        sys.exit(1)
