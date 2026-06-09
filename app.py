"""
app.py — Хугацаа хэтрэлтийн шинжилгээний дашборд
Ажиллуулах: streamlit run app.py
"""
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Хугацаа хэтрэлтийн шинжилгээ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from assets.styles import CSS
from components.sidebar import apply_filters, filter_customer_df, render_sidebar
from tabs import tab_loan, tab_customer
from utils.archive import ARCHIVE_DIR
from utils.config import COL_CUST, COL_AMT, COL_DATE, COL_MAX_AOD, COL_SCORE, COL_STATUS1
from utils.export import to_excel
from utils.preprocess import build_customer_df, preprocess

# ── Archive migration ────────────────────────────────────────────────────────
def _migrate_archive() -> None:
    flag = ARCHIVE_DIR / ".migrated_v2"
    if flag.exists():
        return
    for f in ARCHIVE_DIR.glob("*.parquet"):
        try:
            df = pd.read_parquet(f)
            df.columns = df.columns.str.strip().str.lower()
            if "gender_label" not in df.columns:
                df = preprocess(df)
                df.to_parquet(f, index=False)
        except Exception:
            pass
    flag.touch()

_migrate_archive()

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
df_raw, selected, filters = render_sidebar()
has_cust = COL_CUST in df_raw.columns

# ── ОНОВЧЛОЛ ─────────────────────────────────────────────────────────────────
# ❌ Хуучин: build_customer_df(df_acct) → filter дарах бүрт groupby дахин ажиллана
# ✅ Шинэ:   build_customer_df(df_raw)  → нэг удаа кэшлэнэ
#            filter_customer_df(...)    → зүгээр л мөр шүүнэ → ХУРДАН
# ─────────────────────────────────────────────────────────────────────────────
df_acct      = apply_filters(df_raw, filters)
df_cust_full = build_customer_df(df_raw) if has_cust else pd.DataFrame()
df_cust      = filter_customer_df(df_cust_full, filters) if has_cust else pd.DataFrame()

# ── Header ───────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([5, 2])
with col_h1:
    st.markdown("## 📊 Хугацаа хэтрэлтийн шинжилгээ")
    st.caption(
        f"Үе: **{selected}**  |  "
        f"Данс: **{len(df_acct):,}** / {len(df_raw):,}  |  "
        f"Харилцагч: **{len(df_cust):,}** / {len(df_cust_full):,}"
    )
with col_h2:
    xl = to_excel({
        "loan_level": df_acct[[
            c for c in [COL_CUST, COL_DATE, COL_AMT, COL_STATUS1,
                         COL_SCORE, "max_overdue_day", COL_MAX_AOD, "bucket"]
            if c in df_acct.columns
        ]],
        "customer_level": df_cust,
    })
    st.download_button(
        "⬇️ Excel татах", data=xl,
        file_name=f"analysis_{selected}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.markdown("---")

TAB_LOAN, TAB_CUST = st.tabs(["🏦  Данс түвшин", "👤  Харилцагч түвшин"])

with TAB_LOAN:
    tab_loan.render(df_acct, df_cust, selected)

with TAB_CUST:
    if not has_cust or df_cust.empty:
        st.error(f"'{COL_CUST}' багана байхгүй / дата хоосон.")
    else:
        tab_customer.render(df_cust, selected)

st.markdown("---")
st.caption(f"Хугацаа хэтрэлтийн шинжилгээ · {selected}")
