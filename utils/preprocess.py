"""
preprocess.py — Өгөгдөл цэвэрлэх, баяжуулах функцүүд
"""
import numpy as np
import pandas as pd
import streamlit as st

from utils.config import (
    BUCKET_BINS, BUCKET_LBLS,
    COL_AMT, COL_DATE, COL_IS_OD, COL_ACT_OD,
    COL_MAX_AOD, COL_MAX_OD, COL_SCORE, COL_STATUS1, COL_CUST,
    CUST_ATTRS,
)


@st.cache_data(show_spinner=False)
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Raw DataFrame-ийг цэвэрлэж, derived баганууд нэмнэ."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # ── Төрөл хөрвүүлэлт ─────────────────────────────────────────────────────
    if COL_DATE in df.columns:
        df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")

    for c in [COL_AMT, COL_SCORE, COL_MAX_OD, COL_MAX_AOD]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if COL_MAX_AOD in df.columns:
        df[COL_MAX_AOD] = df[COL_MAX_AOD].fillna(0)

    # ── Цалингийн -1 утга → NaN ───────────────────────────────────────────────
    for c in [
        "slry_last_amt", "slry_last_avg_6m", "slry_last_row_cnt_24m",
        "zms_monthly_payment", "zms_closed_ln_total_amount",
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace(-1, np.nan)

    # ── Boolean баганууд ──────────────────────────────────────────────────────
    def _to_bool(x):
        # bool/тоон утга (Excel-ээс 1.0/0.0 float болж ирэхийг ч зөв таних)
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
        if s in ("FALSE", "0", "0.0", "NO", "N", "F"): return False
        return np.nan

    for c in [COL_IS_OD, COL_ACT_OD]:
        if c in df.columns:
            df[c] = df[c].map(_to_bool)

    if COL_STATUS1 in df.columns:
        df[COL_STATUS1] = df[COL_STATUS1].astype(str).str.strip().replace("N", "C")

    # ── Bucket ────────────────────────────────────────────────────────────────
    if COL_MAX_AOD in df.columns:
        df["bucket"] = pd.cut(
            df[COL_MAX_AOD].fillna(0),
            bins=BUCKET_BINS, labels=BUCKET_LBLS, right=True,
        )

    # ── Огноогийн баганууд ────────────────────────────────────────────────────
    if COL_DATE in df.columns:
        df["loan_ym"]   = df[COL_DATE].dt.to_period("M").astype(str)
        df["loan_year"] = df[COL_DATE].dt.year

    # ── Score band ────────────────────────────────────────────────────────────
    if COL_SCORE in df.columns:
        df["score_band"] = pd.cut(
            df[COL_SCORE],
            bins=[0, 350, 400, 450, 500, 550, 9999],
            labels=["<350", "351–400", "401–450", "451–500", "501–550", "551+"],
            right=True,
        )

    # ── Насны бүлэг ───────────────────────────────────────────────────────────
    if "age" in df.columns:
        age_num = pd.to_numeric(df["age"], errors="coerce")
        df["age_group"] = pd.cut(
            age_num,
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
        "gender":             ("gender_label",   {True: "Эрэгтэй",  False: "Эмэгтэй"}),
        "has_ios":            ("ios_label",      {True: "iOS",       False: "Android"}),
        "is_bio_login":       ("bio_label",      {True: "Биометр",  False: "Нууц үг"}),
        "is_device_remember": ("dev_label",      {True: "Санасан",  False: "Санаагүй"}),
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

    return df


@st.cache_data(show_spinner=False)
def build_customer_df(df: pd.DataFrame) -> pd.DataFrame:
    """Данс түвшний DataFrame-ийг харилцагч түвшинд нэгтгэнэ."""
    if COL_CUST not in df.columns:
        return pd.DataFrame()

    grp  = df.groupby(COL_CUST)
    base = grp[COL_MAX_AOD].agg(
        max_overdue_day="max",
        avg_overdue_day="mean",
        total_loan_cnt ="count",
    ).reset_index()
    base["overdue_loan_cnt"] = grp[COL_MAX_AOD].apply(lambda x: (x > 0).sum()).values

    # Зээлийн төлөвийн тоо
    if COL_STATUS1 in df.columns:
        base["closed_cnt"]   = grp[COL_STATUS1].apply(lambda x: (x == "C").sum()).values
        base["o_max_cnt"]    = grp[COL_STATUS1].apply(lambda x: (x == "O_max").sum()).values
        base["o_active_cnt"] = grp[COL_STATUS1].apply(lambda x: (x == "O_active").sum()).values
        base["status2"]      = grp[COL_STATUS1].apply(
            lambda x: 1 if (x == "O_active").any() else 0).values

    # Зээлийн дүн
    if COL_AMT in df.columns:
        base["total_loan_amt"] = grp[COL_AMT].sum().values
        base["avg_loan_amt"]   = grp[COL_AMT].mean().values
        base["max_loan_amt"]   = grp[COL_AMT].max().values
        base["min_loan_amt"]   = grp[COL_AMT].min().values

    # Оноо
    if COL_SCORE in df.columns:
        base["max_score"] = grp[COL_SCORE].max().values
        base["min_score"] = grp[COL_SCORE].min().values
        base["avg_score"] = grp[COL_SCORE].mean().values

    # Зээлийн хязгаар
    if "calc_lmt" in df.columns:
        df["_calc_lmt_num"] = pd.to_numeric(df["calc_lmt"], errors="coerce")
        base["max_calc_lmt"] = grp["_calc_lmt_num"].max().values
        df.drop(columns=["_calc_lmt_num"], inplace=True, errors="ignore")

    # ZMS
    if "zms_active_ln_cnt" in df.columns:
        base["zms_active_ln_cnt"] = grp["zms_active_ln_cnt"].max().values
    if "zms_closed_ln_total_amount" in df.columns:
        base["zms_closed_ln_total_amount"] = grp["zms_closed_ln_total_amount"].max().values

    # Сарын төлбөр
    if "zms_monthly_payment" in df.columns:
        base["total_monthly_payment"] = grp["zms_monthly_payment"].sum().values
        base["avg_monthly_payment"]   = grp["zms_monthly_payment"].mean().values

    # Демо + цалингийн attr (first)
    extra = [
        "gender_label","ios_label","bio_label","dev_label","slry_cont_label",
        "marital_label","location_type","age_group","score_band",
    ]
    attr_cols = [c for c in CUST_ATTRS if c in df.columns]
    all_first = list(dict.fromkeys(attr_cols + [c for c in extra if c in df.columns]))
    if all_first:
        attrs = grp[all_first].first().reset_index()
        base  = base.merge(attrs, on=COL_CUST, how="left")

    # DTI
    if "slry_last_amt" in base.columns and "total_monthly_payment" in base.columns:
        slry = pd.to_numeric(base["slry_last_amt"], errors="coerce")
        pmt  = pd.to_numeric(base["total_monthly_payment"], errors="coerce")
        base["dti_ratio"] = (pmt / slry.replace(0, np.nan)).round(3)

    # Зээл/Цалин харьцаа
    if "slry_last_avg_6m" in base.columns and "total_loan_amt" in base.columns:
        slry6 = pd.to_numeric(base["slry_last_avg_6m"], errors="coerce")
        base["loan_to_salary_ratio"] = (
            pd.to_numeric(base["total_loan_amt"], errors="coerce") /
            slry6.replace(0, np.nan)
        ).round(2)

    # Хэтрэлтийн ангилал
    _OD_BINS = [-1, 0, 1, 5, 10, 15, 30, 9999]
    _OD_LBLS = ["0","1","2–5","6–10","11–15","16–30","30+"]
    base["overdue_band"]   = pd.cut(
        base["max_overdue_day"].astype(float),
        bins=_OD_BINS, labels=_OD_LBLS, right=True,
    )
    base["overdue_status"] = base["overdue_band"].astype(str)
    base["has_overdue"]    = base["overdue_loan_cnt"] > 0

    return base
