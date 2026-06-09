"""
sidebar.py — Sidebar: upload, period selector, filters
"""
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.archive import (
    delete_period, list_periods, load_meta,
    load_period, save_period,
)
from utils.config import COL_DATE, COL_MAX_AOD, COL_STATUS1
from utils.preprocess import preprocess

ARCHIVE_DIR = Path("archive")

MONTH_MN = {f"{i:02d}": f"{i}-р сар" for i in range(1, 13)}


def _period_label(p: str) -> str:
    parts = p.split("-")
    m = MONTH_MN.get(parts[1], parts[1]) if len(parts) >= 2 else p
    r = load_meta(p).get("rows", "")
    return f"{m}  ({r:,} данс)" if r else m


@st.cache_data(show_spinner="Өгөгдөл ачаалж байна…")
def _get_df(period: str) -> pd.DataFrame:
    df = load_period(period)
    if "gender_label" not in df.columns or "age_group" not in df.columns:
        df = preprocess(df)
    return df


def render_sidebar() -> tuple[pd.DataFrame, str, dict]:
    """
    Sidebar харуулж, filtered raw df болон сонгосон period,
    filter утгуудыг буцаана.

    Returns
    -------
    df_raw   : preprocess хийгдсэн бүрэн DataFrame
    selected : сонгосон period string ("2026-04")
    filters  : sidebar filter утгуудын dict
    """
    with st.sidebar:
        st.markdown("## 📂 Өгөгдөл")
        st.markdown("---")

        # ── ① Upload ────────────────────────────────────────────────────────
        st.markdown("**① Файл оруулах**")
        uploaded     = st.file_uploader(
            "Excel / CSV", type=["xlsx", "xls", "csv"],
            label_visibility="collapsed",
        )
        period_input = st.text_input(
            "Он сар (жишээ: 2026-04)",
            value=datetime.now().strftime("%Y-%m"),
        )

        if uploaded and st.button("💾 Хадгалах", type="primary", use_container_width=True):
            try:
                raw = (
                    pd.read_csv(uploaded)
                    if uploaded.name.endswith(".csv")
                    else pd.read_excel(uploaded)
                )
                raw.columns = raw.columns.str.strip().str.lower()
                missing = [c for c in [COL_STATUS1, COL_MAX_AOD] if c not in raw.columns]
                if missing:
                    st.error(f"Дутуу багана: {', '.join(missing)}")
                else:
                    save_period(preprocess(raw), period_input, filename=uploaded.name)
                    st.success(f"✓ {period_input} — {len(raw):,} данс")
                    st.rerun()
            except Exception as e:
                st.error(f"Алдаа: {e}")

        st.markdown("---")

        # ── ② Period selector ────────────────────────────────────────────────
        periods = list_periods()
        if not periods:
            st.info("Файл upload хийгээгүй байна.")
            st.stop()

        st.markdown("**② Үе сонгох**")
        year_map: dict[str, list[str]] = defaultdict(list)
        for p in periods:
            year_map[p.split("-")[0]].append(p)

        sel_year = st.selectbox(
            "Он:", sorted(year_map.keys(), reverse=True),
            label_visibility="collapsed",
        )
        selected = st.selectbox(
            "Сар:", sorted(year_map[sel_year], reverse=True),
            format_func=_period_label,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── ③ Filters ────────────────────────────────────────────────────────
        st.markdown("**③ Шүүлтүүр**")
        df_raw = _get_df(selected)

        # Огноо
        date_range = None
        if COL_DATE in df_raw.columns and df_raw[COL_DATE].notna().any():
            d_min = df_raw[COL_DATE].min().date()
            d_max = df_raw[COL_DATE].max().date()
            if d_min < d_max:
                dr = st.date_input(
                    "📅 Огноо", value=(d_min, d_max),
                    min_value=d_min, max_value=d_max,
                )
                if isinstance(dr, (list, tuple)) and len(dr) == 2:
                    date_range = dr

        # Нас
        age_range = None
        if "age" in df_raw.columns and df_raw["age"].notna().any():
            _age = pd.to_numeric(df_raw["age"], errors="coerce")
            age_range = st.slider(
                "👤 Нас",
                int(_age.min()), int(_age.max()),
                (int(_age.min()), int(_age.max())),
            )

        # Хугацаа хэтрэлт
        od_range = None
        if COL_MAX_AOD in df_raw.columns and df_raw[COL_MAX_AOD].notna().any():
            od_min = int(df_raw[COL_MAX_AOD].min())
            od_max = int(df_raw[COL_MAX_AOD].max())
            od_range = st.slider(
                "⏱️ Хугацаа хэтрэлт (хоног)", od_min, od_max, (od_min, od_max)
            )

        # Жендэр
        g_opts = sorted(df_raw["gender_label"].dropna().unique()) if "gender_label" in df_raw.columns else []
        g_sel  = st.multiselect("⚥ Жендэр", g_opts, default=g_opts)

        # Боловсрол
        e_opts = sorted(df_raw["edu_name"].dropna().unique()) if "edu_name" in df_raw.columns else []
        e_sel  = st.multiselect("🎓 Боловсрол", e_opts, default=e_opts)

        # Гэрлэлтийн байдал
        m_opts = sorted(df_raw["marital_label"].dropna().unique()) if "marital_label" in df_raw.columns else []
        m_sel  = st.multiselect("💍 Гэрлэлтийн байдал", m_opts, default=m_opts)

        # Байршил
        lt_sel = st.radio(
            "📍 Байршил", ["Бүгд", "Улаанбаатар", "Орон нутаг"], horizontal=True
        )

        # Төлөв
        s1_opts = sorted(df_raw[COL_STATUS1].dropna().unique()) if COL_STATUS1 in df_raw.columns else []
        s1_sel  = st.multiselect("🏷️ Төлөв", s1_opts, default=s1_opts)

        st.markdown("---")
        if st.button(f"🗑️ {selected} устгах", use_container_width=True):
            delete_period(selected)
            st.rerun()

        # ── Cache & migrate ──────────────────────────────────────────────────
        with st.expander("⚙️ Cache & дахин боловсруулах"):
            st.caption("Насны бүлэг эсвэл бусад derived баганууд өөрчлөгдсөн бол дарна уу.")
            if st.button("🔄 Бүх архивыг дахин боловсруулах", use_container_width=True):
                flag = ARCHIVE_DIR / ".migrated_v2"
                if flag.exists():
                    flag.unlink()
                for f in ARCHIVE_DIR.glob("*.parquet"):
                    try:
                        df_m = pd.read_parquet(f)
                        df_m.columns = df_m.columns.str.strip().str.lower()
                        df_m = preprocess(df_m)
                        df_m.to_parquet(f, index=False)
                    except Exception:
                        pass
                st.cache_data.clear()
                st.success("✓ Дахин боловсруулж дууслаа!")
                st.rerun()

            if st.button("🗑️ Бүх архив устгах", use_container_width=True):
                for f in list(ARCHIVE_DIR.glob("*.parquet")):
                    f.unlink()
                for f in list(ARCHIVE_DIR.glob("*.json")):
                    f.unlink()
                for f in list(ARCHIVE_DIR.glob(".*")):
                    f.unlink()
                st.cache_data.clear()
                st.success("✓ Бүх архив устгагдлаа!")
                st.rerun()

    filters = {
        "date_range": date_range,
        "age_range":  age_range,
        "od_range":   od_range,
        "gender":     g_sel,
        "edu":        e_sel,
        "marital":    m_sel,
        "location":   lt_sel,
        "status1":    s1_sel,
    }
    return df_raw, selected, filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Sidebar filter утгуудыг DataFrame-д хэрэгжүүлнэ.
    Данс болон харилцагч түвшний DataFrame хоёулаа дамжиж болно.
    """
    out = df.copy()
    f   = filters

    if COL_STATUS1 in out.columns and f["status1"]:
        out = out[out[COL_STATUS1].isin(f["status1"])]

    if "gender_label" in out.columns and f["gender"]:
        out = out[out["gender_label"].isin(f["gender"])]

    if f["age_range"] and "age" in out.columns:
        out = out[pd.to_numeric(out["age"], errors="coerce").between(*f["age_range"])]

    if "marital_label" in out.columns and f["marital"]:
        out = out[out["marital_label"].isin(f["marital"])]

    if "edu_name" in out.columns and f["edu"]:
        out = out[out["edu_name"].isin(f["edu"])]

    if f["location"] != "Бүгд" and "location_type" in out.columns:
        out = out[out["location_type"] == f["location"]]

    if f["od_range"] and COL_MAX_AOD in out.columns:
        out = out[out[COL_MAX_AOD].between(*f["od_range"])]

    if f["date_range"] and COL_DATE in out.columns:
        lo, hi = f["date_range"]
        out = out[out[COL_DATE].dt.date.between(lo, hi)]

    return out.copy()


def filter_customer_df(df_cust: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Харилцагч түвшний DataFrame-д sidebar filter хэрэгжүүлнэ.
    build_customer_df(df_raw)-г нэг удаа тооцоод энэ функцээр шүүнэ
    → filter дарах бүрт дахин groupby/merge хийхгүй тул ХУРДАН.
    """
    out = df_cust.copy()
    f   = filters

    if "gender_label" in out.columns and f["gender"]:
        out = out[out["gender_label"].isin(f["gender"])]

    if f["age_range"] and "age" in out.columns:
        out = out[pd.to_numeric(out["age"], errors="coerce").between(*f["age_range"])]

    if "marital_label" in out.columns and f["marital"]:
        out = out[out["marital_label"].isin(f["marital"])]

    if "edu_name" in out.columns and f["edu"]:
        out = out[out["edu_name"].isin(f["edu"])]

    if f["location"] != "Бүгд" and "location_type" in out.columns:
        out = out[out["location_type"] == f["location"]]

    # od_range filter — харилцагч түвшинд 0 хоногтой (хэвийн) харилцагчийг
    # үргэлж оруулна. Slider-ийг "1–30" болгоход хэвийн харилцагчид шүүгдэж
    # гарвал rate% тооцоо алдаатай болно (бүгд 100% болдог).
    if f["od_range"] and "max_overdue_day" in out.columns:
        lo, hi = f["od_range"]
        if lo > 0:
            # lo > 0: хэвийн (0 хоног) + slider хязгаарт багтах хэтрэлттэй
            out = out[
                (out["max_overdue_day"] == 0) |
                (out["max_overdue_day"].between(lo, hi))
            ]
        else:
            # lo == 0: хэвийн шүүлт
            out = out[out["max_overdue_day"].between(lo, hi)]

    # status1 filter — харилцагч түвшинд O_active байсан эсэхээр шүүнэ
    if f["status1"]:
        status_conditions = []
        if "C" in f["status1"] and "closed_cnt" in out.columns:
            status_conditions.append(out["closed_cnt"] > 0)
        if "O_max" in f["status1"] and "o_max_cnt" in out.columns:
            status_conditions.append(out["o_max_cnt"] > 0)
        if "O_active" in f["status1"] and "o_active_cnt" in out.columns:
            status_conditions.append(out["o_active_cnt"] > 0)
        if status_conditions:
            import functools, operator
            mask = functools.reduce(operator.or_, status_conditions)
            out  = out[mask]

    return out.copy()
