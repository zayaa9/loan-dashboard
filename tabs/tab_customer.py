"""
tab_customer.py — 👤 Харилцагч түвшний таб (C1–C10)
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.charts import layout, corr_box
from utils.config import (
    AXIS, BUCKET_BINS, BUCKET_LBLS,
    CATEGORY_PAIRS, CORR_COLS, CUST_DISPLAY_COLS,
    COL_CUST, COL_MAX_AOD, COL_STATUS1, SCORE_COLS,
)

OD = "max_overdue_day"  # shorthand


def render(df_cust: pd.DataFrame, selected: str) -> None:
    if df_cust.empty:
        st.error("Харилцагчийн дата хоосон.")
        return

    od_s  = df_cust[OD] if OD in df_cust.columns else pd.Series(dtype=float)
    n_tot = len(df_cust)

    # ── KPI ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    if "total_loan_amt" in df_cust.columns:
        ka, kb, kc, kd = st.columns(4)
        ka.metric("Нийт зээлийн дүн", f"₮{df_cust['total_loan_amt'].sum()/1e9:.2f} тэрбум")
        kb.metric("Дундаж дүн/хүн",   f"₮{df_cust['total_loan_amt'].mean()/1e6:.1f} сая")
        kc.metric("Олон зээлтэй (+1)",
            f"{int((df_cust['total_loan_cnt']>1).sum()):,}" if "total_loan_cnt" in df_cust.columns else "–")
        kd.metric("Дундаж зээл/хүн",
            f"{df_cust['total_loan_cnt'].mean():.1f}" if "total_loan_cnt" in df_cust.columns else "–")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Нийт харилцагч",     f"{n_tot:,}")
    k2.metric("Хэтрэлттэй",
        f"{df_cust['has_overdue'].sum():,}" if "has_overdue" in df_cust.columns else "–",
        f"{df_cust['has_overdue'].mean()*100:.1f}%" if "has_overdue" in df_cust.columns else None,
        delta_color="off")
    k3.metric("Дундаж MAX хэтрэлт", f"{od_s.mean():.1f} хон." if len(od_s) else "–")
    k4.metric("30+ хоног (MAX)",
        f"{int((od_s>30).sum()):,}" if len(od_s) else "–",
        f"{int((od_s>30).sum())/max(n_tot,1)*100:.1f}%" if len(od_s) else None,
        delta_color="off")

    # ── Sub-tabs ──────────────────────────────────────────────────────────────
    C1, CSEG, C3, C6, C7, C8, C9, C10 = st.tabs([
        "📈 Тархалт",
        "🧬 Хэтрэлтийн бүлгийн профайл",
        "🏷️ Категори",
        "💰 Цалингийн шинжилгээ",
        "🏷️ Зээлийн дүн & DTI",
        "🎯 Score шинжилгээ",
        "📊 Корреляц & scatter",
        "🗂️ Өгөгдөл",
    ])

    with C1:   _render_distribution(df_cust, n_tot)
    with CSEG: _render_segment_profile(df_cust)
    with C3:   _render_category(df_cust)
    with C6:   _render_salary(df_cust)
    with C7:   _render_dti(df_cust)
    with C8:   _render_score(df_cust)
    with C9:   _render_correlation(df_cust)
    with C10:  _render_data(df_cust, selected)


# ─────────────────────────────────────────────────────────────────────────────
# C1 — Тархалт
# ─────────────────────────────────────────────────────────────────────────────
def _render_distribution(df: pd.DataFrame, n_tot: int) -> None:
    _od = df[OD] if OD in df.columns else pd.Series(dtype=float)

    # Bucket KPI
    bk_c = st.columns(7)
    bk_c[0].metric("Хэвийн (0)",
        f"{int((_od==0).sum()):,}" if len(_od) else "–",
        f"{(_od==0).sum()/max(n_tot,1)*100:.1f}%", delta_color="off")
    for i, (lbl,lo,hi) in enumerate([("1",1,1),("2–5",2,5),("6–10",6,10),("11–15",11,15),("16–30",16,30),("30+",31,9999)]):
        _n = int(_od.between(lo,hi).sum()) if len(_od) else 0
        bk_c[i+1].metric(lbl, f"{_n:,}", f"{_n/max(n_tot,1)*100:.1f}%", delta_color="off")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sh">MAX хэтрэлт — гистограм</div>', unsafe_allow_html=True)
        fig = px.histogram(df, x=OD, nbins=32, color_discrete_sequence=["#1d9e75"])
        fig.add_vline(x=30, line_dash="dash", line_color="#e24b4a",
            annotation_text="30 хоног", annotation_font=dict(color="#e24b4a"))
        layout(fig, height=280, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sh">Зээлийн тоо ба MAX хэтрэлт</div>', unsafe_allow_html=True)
        if "total_loan_cnt" in df.columns:
            fig4 = px.scatter(df, x="total_loan_cnt", y=OD,
                color="overdue_status" if "overdue_status" in df.columns else None,
                color_discrete_sequence=["#1d9e75","#F5A623","#E8813A","#E24B4A"],
                opacity=0.55, trendline="ols",
                labels={"total_loan_cnt":"Зээлийн тоо", OD:"MAX хэтрэлт (хоног)", "overdue_status":"Хэтрэлтийн байдал"})
            layout(fig4, height=280)
            st.plotly_chart(fig4, use_container_width=True)
            _corr4 = df[["total_loan_cnt",OD]].dropna().corr().iloc[0,1]
            msg, cls = corr_box(_corr4,
                "Зээлийн тоо нэмэгдэхэд хэтрэлт нэмэгдэх хандлагатай — олон зээлтэй харилцагчид санхүүгийн дарамттай байж болзошгүй.",
                "Зээлийн тоо нэмэгдэхэд хэтрэлт буурах хандлагатай — олон зээлтэй харилцагчид харилцангуй хариуцлагатай байна.",
                "Зээлийн тоо болон хэтрэлтийн хоорондын шугаман хамаарал бараг байхгүй байна.",
            )
            st.markdown(f'<div class="{cls}">📊 <b>Корреляц: {_corr4:+.3f}</b> — {msg}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sh">Зээлийн тооноор нэгтгэсэн хүснэгт</div>', unsafe_allow_html=True)
    if "total_loan_cnt" in df.columns and "has_overdue" in df.columns:
        seg = df.groupby("total_loan_cnt").agg(
            Харилцагч=("total_loan_cnt","count"),
            Дундаж_MAX=(OD,"mean"), Медиан=(OD,"median"),
            Хэтэрсэн=("has_overdue","sum"),
        ).reset_index().rename(columns={"total_loan_cnt":"Зээлийн тоо"})
        seg["Хэтрэлт %"] = (seg["Хэтэрсэн"]/seg["Харилцагч"]*100).round(1)
        seg["Дундаж_MAX"] = seg["Дундаж_MAX"].round(1)
        st.dataframe(seg, use_container_width=True, height=260)


# ─────────────────────────────────────────────────────────────────────────────
# CSEG — Хэтрэлтийн бүлгийн профайл
# ─────────────────────────────────────────────────────────────────────────────
SEG_ORDER  = ["0 (хэвийн)", "1–15 хоног", "16–30 хоног", "30+ хоног"]
SEG_COLORS = {"0 (хэвийн)": "#1d9e75", "1–15 хоног": "#f59e0b",
              "16–30 хоног": "#dc2626", "30+ хоног": "#7f1d1d"}

_SEG_NUM = {
    "age": "Нас", "fin_score": "Санхүүгийн оноо", "psy_score": "Сэтгэл зүйн оноо",
    "total_score_sr": "Нийт оноо (SR)", "slry_last_amt": "Сүүлийн цалин (₮)",
    "slry_last_avg_6m": "6 сарын дундаж цалин (₮)", "slry_last_row_cnt_24m": "Цалингийн бичилт (24с)",
    "zms_active_ln_cnt": "Идэвхтэй зээлийн тоо (ZMS)", "zms_monthly_payment": "Сарын зээлийн төлбөр (₮)",
    "zms_closed_ln_total_amount": "Хаагдсан зээлийн нийт дүн (₮)",
}
_SEG_BOOL = {
    "has_ios": "iOS хэрэглэгч", "is_bio_login": "Биометр нэвтрэлт",
    "is_device_remember": "Төхөөрөмж санасан", "mobile_no": "Гар утасны дугаартай",
    "slry_has_cont_salary_3m": "Тасралтгүй цалин 3 сар", "has_active_overdue_loan": "Идэвхтэй хэтрэлттэй зээл",
}
_SEG_CAT = {
    "gender_label": "Жендэр", "marital_label": "Гэрлэлтийн байдал",
    "edu_name": "Боловсрол", "location_type": "Байршил (УБ / Орон нутаг)",
    "slry_cont_label": "Цалингийн тасралтгүй байдал",
}


def _seg_to_num(s: pd.Series) -> pd.Series:
    """bool / 1-0 / текст утгыг 1.0 / 0.0 / NaN болгож хувиргана."""
    def f(v):
        if v in (True, 1, 1.0, "1", "1.0", "True", "TRUE", "YES", "Y", "T"):   return 1.0
        if v in (False, 0, 0.0, "0", "0.0", "False", "FALSE", "NO", "N", "F"): return 0.0
        return np.nan
    return s.map(f)


def _render_segment_profile(df: pd.DataFrame) -> None:
    if OD not in df.columns:
        st.info("Хэтрэлтийн өгөгдөл байхгүй байна.")
        return

    d = df.copy()
    d["_seg"] = pd.cut(
        d[OD].fillna(0).astype(float),
        bins=[-1, 0, 15, 30, np.inf], labels=SEG_ORDER, right=True,
    )

    st.caption(
        "Харилцагчдыг хамгийн их **идэвхтэй хэтрэлтийн хоногоор** 4 бүлэгт хувааж, "
        "ямар шинж чанараараа ялгарч байгааг харьцуулав."
    )

    # ── Бүлгийн хэмжээ ────────────────────────────────────────────────────────
    cnt = d["_seg"].value_counts().reindex(SEG_ORDER).fillna(0).astype(int)
    cc1, cc2 = st.columns([2, 3])
    with cc1:
        tbl = pd.DataFrame({"Бүлэг": SEG_ORDER, "Харилцагч": cnt.values})
        tbl["Хувь"] = (tbl["Харилцагч"] / max(tbl["Харилцагч"].sum(), 1) * 100).round(1).astype(str) + "%"
        st.dataframe(tbl, hide_index=True, use_container_width=True)
    with cc2:
        figc = px.bar(x=SEG_ORDER, y=cnt.values, color=SEG_ORDER,
            color_discrete_map=SEG_COLORS, text=cnt.values,
            labels={"x": "Бүлэг", "y": "Харилцагчийн тоо"})
        layout(figc, height=260, showlegend=False)
        st.plotly_chart(figc, use_container_width=True)

    # ── Тоон үзүүлэлтийн дундаж ───────────────────────────────────────────────
    num_av = {k: v for k, v in _SEG_NUM.items() if k in d.columns}
    if num_av:
        st.markdown('<div class="sh">Тоон үзүүлэлтийн дундаж — бүлгээр</div>', unsafe_allow_html=True)
        rows = []
        for k, v in num_av.items():
            means = pd.to_numeric(d[k], errors="coerce").groupby(d["_seg"], observed=False).mean().reindex(SEG_ORDER)
            rows.append({"Үзүүлэлт": v, **{s: (round(means[s], 1) if pd.notna(means[s]) else "–") for s in SEG_ORDER}})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        sel = st.selectbox("Тоон үзүүлэлт сонгож график харах:",
            list(num_av.keys()), format_func=lambda x: num_av[x], key="seg_num_sel")
        means = pd.to_numeric(d[sel], errors="coerce").groupby(d["_seg"], observed=False).mean().reindex(SEG_ORDER)
        fign = px.bar(x=SEG_ORDER, y=means.values, color=SEG_ORDER,
            color_discrete_map=SEG_COLORS,
            text=[f"{v:,.1f}" if pd.notna(v) else "" for v in means.values],
            labels={"x": "Бүлэг", "y": num_av[sel]})
        fign.update_traces(textposition="outside")
        layout(fign, height=320, showlegend=False)
        st.plotly_chart(fign, use_container_width=True)

    # ── Эзлэх хувь (тийм %) — boolean ─────────────────────────────────────────
    bool_av = {k: v for k, v in _SEG_BOOL.items() if k in d.columns}
    if bool_av:
        st.markdown('<div class="sh">Эзлэх хувь (тийм / TRUE %) — бүлгээр</div>', unsafe_allow_html=True)
        rows = []
        for k, v in bool_av.items():
            pct = (_seg_to_num(d[k]).groupby(d["_seg"], observed=False).mean() * 100).reindex(SEG_ORDER)
            rows.append({"Үзүүлэлт": v, **{s: (f"{pct[s]:.1f}%" if pd.notna(pct[s]) else "–") for s in SEG_ORDER}})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # ── Ангиллын хувьсагчийн тархалт ──────────────────────────────────────────
    cat_av = {k: v for k, v in _SEG_CAT.items() if k in d.columns}
    if cat_av:
        st.markdown('<div class="sh">Ангиллын хувьсагчийн тархалт — бүлгээр (%)</div>', unsafe_allow_html=True)
        selc = st.selectbox("Ангиллын хувьсагч сонгох:",
            list(cat_av.keys()), format_func=lambda x: cat_av[x], key="seg_cat_sel")
        ct = pd.crosstab(d["_seg"], d[selc].astype(str), normalize="index").reindex(SEG_ORDER) * 100
        long = ct.reset_index().melt(id_vars="_seg", var_name=cat_av[selc], value_name="Хувь")
        figk = px.bar(long, x="_seg", y="Хувь", color=cat_av[selc], barmode="stack",
            category_orders={"_seg": SEG_ORDER},
            labels={"_seg": "Бүлэг", "Хувь": "Хувь (%)"})
        layout(figk, height=360)
        st.plotly_chart(figk, use_container_width=True)
        st.dataframe(
            ct.round(1).reset_index().rename(columns={"_seg": "Бүлэг"}),
            use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# C3 — Категори
# ─────────────────────────────────────────────────────────────────────────────
def _dual_category_bar(df: pd.DataFrame, col: str, h: int = 340, min_cnt: int = 3):
    """Категориас хэтрэлтийн дундаж + rate dual-axis chart."""
    if col not in df.columns or "has_overdue" not in df.columns:
        return None
    d = df.groupby(col, observed=True).agg(
        нийт   =(col,          "count"),
        дундаж =(OD,           "mean"),
        хэтэрсэн=("has_overdue","sum"),
    ).reset_index()
    d = d[d["нийт"] >= min_cnt].copy()
    d["rate"]   = (d["хэтэрсэн"]/d["нийт"]*100).round(1)
    d["дундаж"] = d["дундаж"].round(2)
    d = d.sort_values("дундаж")
    if d.empty:
        return None

    cats      = d[col].astype(str).tolist()
    bar_max   = d["дундаж"].max()
    bar_colors = [
        f"rgba({int(26+(226-26)*v)},{int(115+(75-115)*v)},{int(232+(74-232)*v)},0.82)"
        for v in [x/max(bar_max,1) for x in d["дундаж"]]
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cats, y=d["дундаж"], name="Дундаж хоног",
        marker_color=bar_colors,
        text=d["дундаж"].round(1), textposition="outside",
        textfont=dict(color="#111",size=11), yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=cats, y=d["rate"], name="Хэтрэлтийн rate %",
        mode="lines+markers+text",
        line=dict(color="#e24b4a",width=2.5),
        marker=dict(size=8, color="#e24b4a", line=dict(color="#fff",width=1.5)),
        text=d["rate"].astype(str)+"%",
        textposition="top center", textfont=dict(color="#e24b4a",size=11), yaxis="y2",
    ))
    layout(fig, height=h,
        xaxis=dict(**{**AXIS,"tickfont":dict(color="#111",size=11)}, tickangle=-30, automargin=True),
        yaxis=dict(**AXIS, title="Дундаж хоног"),
        yaxis2=dict(overlaying="y", side="right", title="Хэтрэлтийн rate %",
            ticksuffix="%", tickfont=dict(color="#e24b4a",size=11),
            title_font=dict(color="#e24b4a",size=12),
            gridcolor="rgba(0,0,0,0)", range=[0, min(d["rate"].max()*2, 100)]),
        legend=dict(font=dict(color="#111",size=11), bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#ddd", borderwidth=1, orientation="v",
            x=0.01, xanchor="left", y=0.99, yanchor="top"),
        barmode="group",
        margin=dict(l=10, r=20, t=36, b=8),
    )
    return fig, d


def _render_category(df: pd.DataFrame) -> None:
    # Насны бүлгээр stacked bar
    st.markdown('<div class="sh">Насны бүлгээр — хэтрэлтийн байдал %</div>', unsafe_allow_html=True)
    if "age_group" in df.columns and "overdue_status" in df.columns:
        cr = pd.crosstab(df["age_group"], df["overdue_status"], normalize="index") * 100
        cr = cr.reset_index().melt(id_vars="age_group", var_name="Байдал", value_name="Хувь")
        fig2 = px.bar(cr, x="age_group", y="Хувь", color="Байдал",
            color_discrete_sequence=["#1d9e75","#F5A623","#E8813A","#E24B4A"])
        layout(fig2, height=300, barmode="stack")
        st.plotly_chart(fig2, use_container_width=True)

    # Бүх категорийн dual-bar
    FIXED_H = 340
    for i in range(0, len(CATEGORY_PAIRS), 2):
        row_pairs = CATEGORY_PAIRS[i:i+2]
        cols_ = st.columns(2)
        for j in range(2):
            with cols_[j]:
                if j < len(row_pairs):
                    col, title = row_pairs[j]
                    st.markdown(f'<div class="sh">{title}</div>', unsafe_allow_html=True)
                    res = _dual_category_bar(df, col, FIXED_H)
                    if res:
                        fig, _ = res
                        st.plotly_chart(fig, use_container_width=True)

    # Байршлаар horizontal bar
    st.markdown('<div class="sh">Байршлаар — дундаж хоног & хэтрэлтийн rate (тоо ≥ 5)</div>', unsafe_allow_html=True)
    if "location" in df.columns and "has_overdue" in df.columns:
        ld = df.groupby("location", observed=True).agg(
            нийт    =("location",    "count"),
            дундаж  =(OD,            "mean"),
            хэтэрсэн=("has_overdue", "sum"),
        ).reset_index()
        ld = ld[ld["нийт"] >= 5].copy()
        ld["rate"]   = (ld["хэтэрсэн"]/ld["нийт"]*100).round(1)
        ld["дундаж"] = ld["дундаж"].round(2)
        ld = ld.sort_values("дундаж", ascending=True)

        fig_loc = go.Figure()
        fig_loc.add_trace(go.Bar(
            y=ld["location"].astype(str), x=ld["дундаж"],
            name="Дундаж хоног", orientation="h",
            marker=dict(color=ld["дундаж"], colorscale=[[0,"#1a73e8"],[1,"#e24b4a"]], showscale=False),
            text=ld["дундаж"].round(1), textposition="outside",
            textfont=dict(color="#111",size=11), xaxis="x1",
        ))
        fig_loc.add_trace(go.Scatter(
            y=ld["location"].astype(str), x=ld["rate"],
            name="Хэтрэлтийн rate %", mode="markers+text",
            marker=dict(size=9, color="#e24b4a", symbol="diamond", line=dict(color="#fff",width=1.2)),
            text=ld["rate"].astype(str)+"%", textposition="middle right",
            textfont=dict(color="#e24b4a",size=10), xaxis="x2",
        ))
        h_loc = max(380, len(ld)*26)
        layout(fig_loc, height=h_loc,
            xaxis =dict(**AXIS, title="Дундаж хоног"),
            xaxis2=dict(overlaying="x", side="top", title="Хэтрэлтийн rate %",
                ticksuffix="%", tickfont=dict(color="#e24b4a",size=11),
                title_font=dict(color="#e24b4a",size=12),
                gridcolor="rgba(0,0,0,0)", range=[0, min(ld["rate"].max()*2.2, 100)]),
            legend=dict(font=dict(color="#111",size=11), bgcolor="rgba(255,255,255,0.88)",
                bordercolor="#ddd", borderwidth=1, orientation="v",
                x=0.01, xanchor="left", y=0.99, yanchor="top"),
            margin=dict(l=10, r=20, t=36, b=16),
        )
        st.plotly_chart(fig_loc, use_container_width=True)

    # Нэгтгэл хүснэгт
    st.markdown('<div class="sh">Бүх категорийн нэгтгэл хүснэгт</div>', unsafe_allow_html=True)
    summ_rows = []
    for col, title in CATEGORY_PAIRS:
        if col not in df.columns or "has_overdue" not in df.columns:
            continue
        for val, grp in df.groupby(col, observed=True):
            summ_rows.append({
                "Хувьсагч": title, "Утга": str(val), "Тоо": len(grp),
                "Хэтрэлтийн rate %": round(grp["has_overdue"].mean()*100, 1),
                "Дундаж хоног": round(grp[OD].mean(), 1),
                "Медиан хоног": round(grp[OD].median(), 1),
            })
    if summ_rows:
        st.dataframe(
            pd.DataFrame(summ_rows).sort_values(["Хувьсагч","Хэтрэлтийн rate %"], ascending=[True,False]),
            use_container_width=True, hide_index=True, height=400)


# ─────────────────────────────────────────────────────────────────────────────
# C6 — Цалингийн шинжилгээ
# ─────────────────────────────────────────────────────────────────────────────
def _render_salary(df: pd.DataFrame) -> None:
    if "slry_last_amt" not in df.columns:
        st.info("Цалингийн мэдээлэл байхгүй байна.")
        return

    sl     = df["slry_last_amt"].dropna()
    od_sl  = df[df["has_overdue"]]["slry_last_amt"].dropna() if "has_overdue" in df.columns else pd.Series()
    nod_sl = df[~df["has_overdue"]]["slry_last_amt"].dropna() if "has_overdue" in df.columns else pd.Series()
    pct_no = df["slry_last_amt"].isna().mean()*100

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Дундаж цалин",   f"₮{sl.mean()/1e6:.2f}M" if len(sl) else "–")
    k2.metric("Медиан цалин",   f"₮{sl.median()/1e6:.2f}M" if len(sl) else "–")
    k3.metric("Мэдээлэлгүй %",  f"{pct_no:.1f}%")
    k4.metric("OD дундаж цалин",  f"₮{od_sl.mean()/1e6:.2f}M" if len(od_sl) else "–")
    k5.metric("NOD дундаж цалин", f"₮{nod_sl.mean()/1e6:.2f}M" if len(nod_sl) else "–")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sh">Цалингийн тархалт (гистограм)</div>', unsafe_allow_html=True)
        tmp = df[["slry_last_amt","has_overdue"]].dropna(subset=["slry_last_amt"])
        tmp = tmp.copy()
        tmp["Бүлэг"] = tmp["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})
        fig = px.histogram(tmp, x="slry_last_amt", color="Бүлэг", nbins=40,
            barmode="overlay", opacity=0.65,
            color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"},
            labels={"slry_last_amt":"Сүүлийн цалин (₮)"})
        layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sh">Цалин vs MAX хэтрэлт (scatter)</div>', unsafe_allow_html=True)
        tmp2 = df[["slry_last_amt", OD, "overdue_status"]].dropna(subset=["slry_last_amt"])
        fig2 = px.scatter(tmp2, x="slry_last_amt", y=OD, color="overdue_status",
            color_discrete_sequence=["#1d9e75","#F5A623","#E8813A","#E24B4A"],
            opacity=0.5, trendline="ols",
            labels={"slry_last_amt":"Цалин (₮)", OD:"MAX хэтрэлт (хоног)"})
        corr = df[["slry_last_amt",OD]].dropna().corr().iloc[0,1]
        layout(fig2, height=300)
        st.plotly_chart(fig2, use_container_width=True)
        msg, cls = corr_box(corr,
            "Цалин өндөр ч хэтрэлт их байгаа нь зээлийн дарамт орлогоос хэтэрсэн байж болзошгүй.",
            "Цалин өндөр байсан харилцагчид хэтрэлт харьцангуй бага — орлого эрсдэлийг бууруулж байна.",
            "Цалин болон хэтрэлтийн хоорондын хамаарал маш сул — цалин дангаараа хэтрэлтийг тайлбарлах чадвар хязгаарлагдмал.",
        )
        st.markdown(f'<div class="{cls}">📊 <b>Корреляц: {corr:+.3f}</b> — {msg}</div>', unsafe_allow_html=True)

    # Цалингийн bucket × rate
    st.markdown('<div class="sh">Цалингийн бүсээр — хэтрэлтийн rate</div>', unsafe_allow_html=True)
    def slry_bucket(x):
        if pd.isna(x): return "Мэдээлэлгүй"
        if x < 500_000:   return "<500K"
        if x < 1_000_000: return "500K–1M"
        if x < 2_000_000: return "1M–2M"
        if x < 3_000_000: return "2M–3M"
        if x < 5_000_000: return "3M–5M"
        return "5M+"
    order = ["Мэдээлэлгүй","<500K","500K–1M","1M–2M","2M–3M","3M–5M","5M+"]
    df = df.copy()
    df["slry_bucket"] = df["slry_last_amt"].apply(slry_bucket)
    sr = df.groupby("slry_bucket").agg(нийт=(COL_CUST,"count"), хэтэрсэн=("has_overdue","sum")).reset_index()
    sr["rate"] = (sr["хэтэрсэн"]/sr["нийт"]*100).round(1)
    sr["slry_bucket"] = pd.Categorical(sr["slry_bucket"], categories=order, ordered=True)
    sr = sr.sort_values("slry_bucket")
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=sr["slry_bucket"], y=sr["нийт"], name="Нийт",
        marker_color="#1a73e8", opacity=0.7,
        text=sr["нийт"], textposition="outside", yaxis="y1"))
    fig3.add_trace(go.Scatter(x=sr["slry_bucket"], y=sr["rate"],
        name="Хэтрэлтийн rate %", mode="lines+markers+text",
        line=dict(color="#e24b4a",width=2.5), marker=dict(size=9),
        text=sr["rate"].astype(str)+"%",
        textposition="top center", textfont=dict(color="#e24b4a",size=11), yaxis="y2"))
    layout(fig3, height=340,
        yaxis=dict(**AXIS, title="Харилцагч"),
        yaxis2=dict(overlaying="y", side="right", title="Rate %",
            ticksuffix="%", tickfont=dict(color="#e24b4a",size=11),
            gridcolor="rgba(0,0,0,0)", range=[0, max(sr["rate"].max()*1.6, 5)]))
    st.plotly_chart(fig3, use_container_width=True)

    # Box + тасралтгүй байдал
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="sh">6 сарын дундаж цалин — OD vs NOD (box)</div>', unsafe_allow_html=True)
        if "slry_last_avg_6m" in df.columns:
            tmp3 = df[["slry_last_avg_6m","has_overdue"]].dropna(subset=["slry_last_avg_6m"]).copy()
            tmp3["Бүлэг"] = tmp3["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})
            fig4 = px.box(tmp3, x="Бүлэг", y="slry_last_avg_6m", color="Бүлэг",
                color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"},
                labels={"slry_last_avg_6m":"6 сарын дундаж цалин (₮)"})
            layout(fig4, height=300, showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

    with c4:
        st.markdown('<div class="sh">Тасралтгүй цалин 3 сар — хэтрэлтийн rate</div>', unsafe_allow_html=True)
        if "slry_cont_label" in df.columns:
            sc = df.groupby("slry_cont_label").agg(
                нийт=(COL_CUST,"count"), хэтэрсэн=("has_overdue","sum")).reset_index()
            sc["rate"] = (sc["хэтэрсэн"]/sc["нийт"]*100).round(1)
            fig5 = px.bar(sc, x="slry_cont_label", y="rate",
                color="slry_cont_label",
                color_discrete_sequence=["#1d9e75","#e24b4a","#f59e0b"],
                text=sc.apply(lambda r: f"{r['rate']}% ({r['нийт']:,})", axis=1),
                labels={"slry_cont_label":"Цалингийн байдал","rate":"Хэтрэлтийн rate %"})
            fig5.update_traces(textposition="outside")
            layout(fig5, height=300, showlegend=False)
            st.plotly_chart(fig5, use_container_width=True)

    # 24 сарын бичилт
    if "slry_last_row_cnt_24m" in df.columns:
        st.markdown('<div class="sh">24 сард цалин төлсөн тоо — хэтрэлтийн шинжилгээ</div>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5:
            tmp_24 = df[["slry_last_row_cnt_24m","has_overdue"]].dropna(subset=["slry_last_row_cnt_24m"]).copy()
            tmp_24["Бүлэг"] = tmp_24["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})
            fig_24a = px.box(tmp_24, x="Бүлэг", y="slry_last_row_cnt_24m", color="Бүлэг",
                color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"},
                labels={"slry_last_row_cnt_24m":"24 сард цалин төлсөн тоо"})
            layout(fig_24a, height=300, showlegend=False)
            st.plotly_chart(fig_24a, use_container_width=True)
            _c24 = df[["slry_last_row_cnt_24m",OD]].dropna().corr().iloc[0,1]
            msg24, cls24 = corr_box(_c24,
                "Цалин тооны өсөлт хэтрэлтийг буурааж чадахгүй байна.",
                "Цалин тогтмол орж байсан харилцагчид хэтрэлт бага — тасралтгүй орлого хамгаалалт болж байна.",
                "24 сарын цалингийн бичилт хэтрэлттэй шугаман хамаарал сул байна.",
            )
            st.markdown(f'<div class="{cls24}">📊 <b>Корреляц: {_c24:+.3f}</b> — {msg24}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# C7 — Зээлийн дүн & DTI
# ─────────────────────────────────────────────────────────────────────────────
def _render_dti(df: pd.DataFrame) -> None:
    ta  = df["total_loan_amt"] if "total_loan_amt" in df.columns else pd.Series()
    dti = df["dti_ratio"].dropna() if "dti_ratio" in df.columns else pd.Series()
    lsr = df["loan_to_salary_ratio"].dropna() if "loan_to_salary_ratio" in df.columns else pd.Series()

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Нийт зээлийн дүн",      f"₮{ta.sum()/1e9:.2f}T" if len(ta) else "–")
    k2.metric("Дундаж зээл/хүн",        f"₮{ta.mean()/1e6:.2f}M" if len(ta) else "–")
    k3.metric("Дундаж DTI",             f"{dti.mean():.2f}" if len(dti) else "–")
    k4.metric("DTI > 0.5 харилцагч",    f"{int((dti>0.5).sum()):,}" if len(dti) else "–", delta_color="inverse")
    k5.metric("Зээл/Цалин дундаж",      f"{lsr.mean():.1f}x" if len(lsr) else "–")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sh">Нийт зээлийн дүн — OD vs NOD (box)</div>', unsafe_allow_html=True)
        if "total_loan_amt" in df.columns and "has_overdue" in df.columns:
            tmp = df[["total_loan_amt","has_overdue"]].copy()
            tmp["Бүлэг"] = tmp["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})
            fig = px.box(tmp, x="Бүлэг", y="total_loan_amt", color="Бүлэг",
                color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"},
                labels={"total_loan_amt":"Нийт зээлийн дүн (₮)"})
            layout(fig, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sh">Зээлийн дүн × MAX хэтрэлт (scatter)</div>', unsafe_allow_html=True)
        if "total_loan_amt" in df.columns and "has_overdue" in df.columns:
            tmp2 = df[["total_loan_amt",OD,"has_overdue"]].dropna().copy()
            tmp2["Бүлэг"] = tmp2["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})
            fig2 = px.scatter(tmp2, x="total_loan_amt", y=OD, color="Бүлэг",
                color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"},
                opacity=0.5, trendline="ols",
                labels={"total_loan_amt":"Нийт зээлийн дүн (₮)",OD:"MAX хэтрэлт (хоног)"})
            corr = tmp2[["total_loan_amt",OD]].corr().iloc[0,1]
            layout(fig2, height=300)
            st.plotly_chart(fig2, use_container_width=True)
            st.caption(f"Корреляц: **{corr:+.3f}**")

    # DTI bucket
    st.markdown('<div class="sh">DTI (Сарын төлбөр / Цалин) — хэтрэлтийн rate</div>', unsafe_allow_html=True)
    if "dti_ratio" in df.columns and "has_overdue" in df.columns:
        def dti_bucket(x):
            if pd.isna(x): return "Мэдээлэлгүй"
            if x <= 0.2: return "≤0.2"
            if x <= 0.4: return "0.2–0.4"
            if x <= 0.6: return "0.4–0.6"
            if x <= 0.8: return "0.6–0.8"
            if x <= 1.0: return "0.8–1.0"
            return ">1.0"
        dti_order = ["Мэдээлэлгүй","≤0.2","0.2–0.4","0.4–0.6","0.6–0.8","0.8–1.0",">1.0"]
        df = df.copy()
        df["dti_bucket"] = df["dti_ratio"].apply(dti_bucket)
        dr = df.groupby("dti_bucket").agg(нийт=(COL_CUST,"count"), хэтэрсэн=("has_overdue","sum")).reset_index()
        dr["rate"] = (dr["хэтэрсэн"]/dr["нийт"]*100).round(1)
        dr["dti_bucket"] = pd.Categorical(dr["dti_bucket"], categories=dti_order, ordered=True)
        dr = dr.sort_values("dti_bucket")

        c3, c4 = st.columns(2)
        with c3:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=dr["dti_bucket"], y=dr["нийт"], name="Нийт",
                marker_color="#1a73e8", opacity=0.7,
                text=dr["нийт"], textposition="outside", yaxis="y1"))
            fig3.add_trace(go.Scatter(x=dr["dti_bucket"], y=dr["rate"],
                name="Rate %", mode="lines+markers+text",
                line=dict(color="#e24b4a",width=2.5), marker=dict(size=9),
                text=dr["rate"].astype(str)+"%",
                textposition="top center", textfont=dict(color="#e24b4a",size=11), yaxis="y2"))
            layout(fig3, height=340,
                yaxis=dict(**AXIS, title="Харилцагч"),
                yaxis2=dict(overlaying="y", side="right", title="Rate %",
                    ticksuffix="%", tickfont=dict(color="#e24b4a",size=11),
                    gridcolor="rgba(0,0,0,0)", range=[0, max(dr["rate"].max()*1.6, 5)]))
            st.plotly_chart(fig3, use_container_width=True)
        with c4:
            st.markdown('<div class="sh">DTI тархалт — OD vs NOD</div>', unsafe_allow_html=True)
            tmp3 = df[["dti_ratio","has_overdue"]].dropna(subset=["dti_ratio"]).copy()
            tmp3["Бүлэг"] = tmp3["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})
            fig4 = px.histogram(tmp3, x="dti_ratio", color="Бүлэг",
                barmode="overlay", opacity=0.65, nbins=30,
                color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"},
                labels={"dti_ratio":"DTI харьцаа"})
            layout(fig4, height=300)
            st.plotly_chart(fig4, use_container_width=True)

    # Зээл/Цалин
    st.markdown('<div class="sh">Зээл/Цалин харьцаа × MAX хэтрэлт</div>', unsafe_allow_html=True)
    if "loan_to_salary_ratio" in df.columns and "has_overdue" in df.columns:
        def lsr_bucket(x):
            if pd.isna(x): return "Мэдээлэлгүй"
            if x <= 1: return "≤1x"
            if x <= 2: return "1–2x"
            if x <= 3: return "2–3x"
            if x <= 5: return "3–5x"
            return ">5x"
        lsr_order = ["Мэдээлэлгүй","≤1x","1–2x","2–3x","3–5x",">5x"]
        df = df.copy()
        df["lsr_bucket"] = df["loan_to_salary_ratio"].apply(lsr_bucket)
        lr = df.groupby("lsr_bucket").agg(нийт=(COL_CUST,"count"), хэтэрсэн=("has_overdue","sum")).reset_index()
        lr["rate"] = (lr["хэтэрсэн"]/lr["нийт"]*100).round(1)
        lr["lsr_bucket"] = pd.Categorical(lr["lsr_bucket"], categories=lsr_order, ordered=True)
        lr = lr.sort_values("lsr_bucket")
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(x=lr["lsr_bucket"], y=lr["нийт"], name="Нийт",
            marker_color="#1a73e8", opacity=0.7,
            text=lr["нийт"], textposition="outside", yaxis="y1"))
        fig5.add_trace(go.Scatter(x=lr["lsr_bucket"], y=lr["rate"],
            name="Rate %", mode="lines+markers+text",
            line=dict(color="#e24b4a",width=2.5), marker=dict(size=9),
            text=lr["rate"].astype(str)+"%",
            textposition="top center", textfont=dict(color="#e24b4a",size=11), yaxis="y2"))
        layout(fig5, height=320,
            yaxis=dict(**AXIS, title="Харилцагч"),
            yaxis2=dict(overlaying="y", side="right", title="Rate %",
                ticksuffix="%", tickfont=dict(color="#e24b4a",size=11),
                gridcolor="rgba(0,0,0,0)", range=[0, max(lr["rate"].max()*1.6, 5)]))
        st.plotly_chart(fig5, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# C8 — Score шинжилгээ
# ─────────────────────────────────────────────────────────────────────────────
def _render_score(df: pd.DataFrame) -> None:
    avail = {k:v for k,v in SCORE_COLS.items() if k in df.columns}
    if not avail:
        st.info("Score баганууд байхгүй байна.")
        return

    BUCK_COLORS = {"0":"#1d9e75","1":"#84cc16","2–5":"#f59e0b","6–10":"#f97316","11–15":"#ef4444","16–30":"#dc2626","30+":"#7f1d1d"}

    # KPI — OD vs NOD
    if "has_overdue" in df.columns:
        od_g, nod_g = df[df["has_overdue"]], df[~df["has_overdue"]]
        cols_k = st.columns(len(avail))
        for i, (col,lbl) in enumerate(avail.items()):
            od_m  = od_g[col].mean()  if col in od_g.columns  else None
            nod_m = nod_g[col].mean() if col in nod_g.columns else None
            diff  = od_m - nod_m if (od_m is not None and nod_m is not None) else None
            cols_k[i].metric(lbl,
                f"OD:{od_m:.1f}" if od_m is not None else "–",
                delta=f"NOD-тай зөрүү: {diff:+.1f}" if diff is not None else None,
                delta_color="inverse")
    st.markdown("---")

    # Histogram
    sel = st.selectbox("Оноо сонгох:", list(avail.keys()), format_func=lambda x: avail.get(x,x), key="score_sel")
    if sel and OD in df.columns:
        tmp = df[[sel,OD]].dropna(subset=[sel,OD]).copy()
        tmp["Bucket"] = pd.Categorical(
            pd.cut(tmp[OD], bins=BUCKET_BINS, labels=BUCKET_LBLS, right=True).astype(str),
            categories=BUCKET_LBLS, ordered=True)
        tmp_2g = df[[sel,"has_overdue"]].dropna(subset=[sel]).copy()
        tmp_2g["Бүлэг"] = tmp_2g["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})

        st.markdown('<div class="sh">① Оноогийн тархалт — Хэвийн vs Хэтрэлттэй</div>', unsafe_allow_html=True)
        fig_h = px.histogram(tmp_2g, x=sel, color="Бүлэг",
            barmode="overlay", opacity=0.65, nbins=40,
            color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"},
            labels={sel: avail.get(sel,sel)})
        layout(fig_h, height=320)
        st.plotly_chart(fig_h, use_container_width=True)

        st.markdown('<div class="sh">② Box plot</div>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            fig_b2 = px.box(tmp_2g, x="Бүлэг", y=sel, color="Бүлэг",
                color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"}, points="outliers")
            fig_b2.update_traces(marker=dict(size=3, opacity=0.4))
            layout(fig_b2, height=360, showlegend=False)
            st.plotly_chart(fig_b2, use_container_width=True)
        with cb:
            fig_bk = px.box(tmp, x="Bucket", y=sel, color="Bucket",
                color_discrete_map=BUCK_COLORS, points=False,
                category_orders={"Bucket": BUCKET_LBLS})
            layout(fig_bk, height=360, showlegend=False)
            st.plotly_chart(fig_bk, use_container_width=True)

    # Score band × rate
    st.markdown('<div class="sh">Score band × хэтрэлтийн rate</div>', unsafe_allow_html=True)
    sel2 = st.selectbox("Оноо сонгох (band):", list(avail.keys()), format_func=lambda x: avail.get(x,x), key="score_band_sel")
    if sel2 in df.columns and "has_overdue" in df.columns:
        mn, mx = df[sel2].min(), df[sel2].max()
        if mn == mx:
            st.info("Оноогийн утга хангалтгүй — filter-г өргөсгөнө үү.")
        else:
            step     = (mx - mn) / 8
            bins     = [mn + i*step for i in range(9)]
            labels_b = [f"{int(bins[i])}–{int(bins[i+1])}" for i in range(8)]
            df = df.copy()
            df["_tmp_band"] = pd.cut(df[sel2], bins=bins, labels=labels_b, include_lowest=True)
            sb = df.groupby("_tmp_band", observed=True).agg(
                нийт=(COL_CUST,"count"), хэтэрсэн=("has_overdue","sum")).reset_index()
            sb["rate"] = (sb["хэтэрсэн"] / sb["нийт"].replace(0, pd.NA) * 100).round(1).fillna(0)

            # ── Динамик range: rate 0 байсан ч шугам харагдана ──────────────
            rate_max   = sb["rate"].max()
            y2_max     = max(rate_max * 1.6, 5)   # хамгийн багадаа 5% харуулна

            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=sb["_tmp_band"].astype(str), y=sb["нийт"],
                name="Нийт", marker_color="#1a73e8", opacity=0.6,
                text=sb["нийт"], textposition="outside", yaxis="y1",
            ))
            fig3.add_trace(go.Scatter(
                x=sb["_tmp_band"].astype(str), y=sb["rate"],
                name="Хэтрэлт %", mode="lines+markers+text",
                line=dict(color="#e24b4a", width=2.5),
                marker=dict(size=9, color="#e24b4a", line=dict(color="#fff", width=1.5)),
                text=[f"{v}%" for v in sb["rate"]],
                textposition="top center",
                textfont=dict(color="#e24b4a", size=11),
                yaxis="y2",
            ))
            layout(fig3, height=360,
                yaxis=dict(**AXIS, title="Харилцагч"),
                yaxis2=dict(
                    overlaying="y", side="right", title="Хэтрэлтийн rate %",
                    ticksuffix="%", tickfont=dict(color="#e24b4a", size=11),
                    title_font=dict(color="#e24b4a", size=12),
                    gridcolor="rgba(0,0,0,0)",
                    range=[0, y2_max],          # ← динамик range
                ),
                legend=dict(font=dict(color="#111",size=11),
                    bgcolor="rgba(255,255,255,0.9)", bordercolor="#ddd", borderwidth=1,
                    x=0.99, xanchor="right", y=0.99, yanchor="top"),
                margin=dict(l=10, r=70, t=32, b=8),
            )
            # Rate бүгд 0 бол анхааруулга харуулна
            if rate_max == 0:
                st.info("💡 Сонгосон filter-д хэтрэлттэй харилцагч байхгүй байна — Rate % = 0%")
            st.plotly_chart(fig3, use_container_width=True)

    # fin_score vs psy_score
    if "fin_score" in df.columns and "psy_score" in df.columns:
        st.markdown('<div class="sh">Санхүүгийн оноо × Сэтгэл зүйн оноо</div>', unsafe_allow_html=True)
        tmp3 = df[["fin_score","psy_score","has_overdue",OD]].dropna(subset=["fin_score","psy_score"]).copy()
        tmp3["Бүлэг"] = tmp3["has_overdue"].map({True:"Хэтрэлттэй",False:"Хэвийн"})
        c3, c4 = st.columns(2)
        with c3:
            fig4 = px.scatter(tmp3, x="fin_score", y="psy_score", color="Бүлэг",
                color_discrete_map={"Хэтрэлттэй":"#e24b4a","Хэвийн":"#1d9e75"}, opacity=0.5,
                labels={"fin_score":"Санхүүгийн оноо","psy_score":"Сэтгэл зүйн оноо"})
            layout(fig4, height=320)
            st.plotly_chart(fig4, use_container_width=True)
        with c4:
            fig5 = px.scatter(tmp3, x="fin_score", y="psy_score", color=OD,
                color_continuous_scale="RdYlGn_r", opacity=0.6,
                labels={"fin_score":"Санхүүгийн оноо","psy_score":"Сэтгэл зүйн оноо", OD:"MAX хэтрэлт (хоног)"})
            layout(fig5, height=320)
            st.plotly_chart(fig5, use_container_width=True)

    # Нэгтгэл хүснэгт
    st.markdown('<div class="sh">Score нэгтгэл хүснэгт — OD vs NOD</div>', unsafe_allow_html=True)
    if "has_overdue" in df.columns:
        rows_s = []
        for col, lbl in avail.items():
            od_v  = df[df["has_overdue"]][col].dropna()
            nod_v = df[~df["has_overdue"]][col].dropna()
            rows_s.append({
                "Оноо": lbl,
                "OD дундаж": round(od_v.mean(),1) if len(od_v) else "–",
                "NOD дундаж": round(nod_v.mean(),1) if len(nod_v) else "–",
                "Зөрүү": round(od_v.mean()-nod_v.mean(),1) if len(od_v) and len(nod_v) else "–",
                "OD медиан": round(od_v.median(),1) if len(od_v) else "–",
                "NOD медиан": round(nod_v.median(),1) if len(nod_v) else "–",
            })
        st.dataframe(pd.DataFrame(rows_s), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# C9 — Корреляц & Scatter
# ─────────────────────────────────────────────────────────────────────────────
def _render_correlation(df: pd.DataFrame) -> None:
    avail_n = {k:v for k,v in CORR_COLS.items() if k in df.columns}

    st.markdown('<div class="sh">Бүх тоон хувьсагчийн хэтрэлттэй корреляц</div>', unsafe_allow_html=True)
    rows_c = []
    for col, lbl in avail_n.items():
        tmp = df[[col,OD]].dropna()
        if len(tmp) > 5:
            rows_c.append({"Хувьсагч": lbl, "Корреляц": round(tmp[col].corr(tmp[OD]),4), "n": len(tmp)})

    if rows_c:
        cdf = pd.DataFrame(rows_c).sort_values("Корреляц")
        figC = go.Figure(go.Bar(
            x=cdf["Корреляц"], y=cdf["Хувьсагч"], orientation="h",
            marker_color=["#E24B4A" if v < 0 else "#1D9E75" for v in cdf["Корреляц"]],
            text=[f"{v:+.4f}  (n={n:,})" for v, n in zip(cdf["Корреляц"], cdf["n"])],
            textposition="outside", textfont=dict(color="#111",size=12)))
        figC.add_vline(x=0, line_color="#888", line_width=1.5)
        layout(figC, height=480, showlegend=False, margin=dict(l=10,r=160,t=32,b=8))
        st.plotly_chart(figC, use_container_width=True)
        st.caption("🟢 Эерэг = хувьсагч нэмэгдэхэд хэтрэлт нэмэгдэнэ  |  🔴 Сөрөг = хэтрэлт багасна")
    st.markdown("---")

    st.markdown('<div class="sh">Тоон хувьсагч сонгоод scatter харах</div>', unsafe_allow_html=True)
    if not avail_n:
        st.info("Тоон хувьсагч олдсонгүй.")
        return
    sel_n = st.selectbox("Хувьсагч:", list(avail_n.keys()), format_func=lambda x: avail_n[x], key="corr_scatter_sel")
    if sel_n:
        color_col = "age_group" if "age_group" in df.columns else None
        tmp2 = df[[sel_n,OD]+([color_col] if color_col else [])].dropna(subset=[sel_n,OD])
        figS = px.scatter(tmp2, x=sel_n, y=OD, color=color_col,
            color_discrete_sequence=px.colors.qualitative.Set2,
            opacity=0.55, trendline="ols",
            labels={sel_n: avail_n[sel_n], OD:"MAX хэтрэлт (хоног)", "age_group":"Насны бүлэг"})
        corr2 = tmp2[[sel_n,OD]].corr().iloc[0,1]
        layout(figS, height=380)
        st.plotly_chart(figS, use_container_width=True)
        st.caption(f"**{avail_n[sel_n]}** × MAX хэтрэлт корреляц: **{corr2:+.4f}**")


# ─────────────────────────────────────────────────────────────────────────────
# C10 — Өгөгдөл
# ─────────────────────────────────────────────────────────────────────────────
def _render_data(df: pd.DataFrame, selected: str) -> None:
    dcols = {k:v for k,v in CUST_DISPLAY_COLS.items() if k in df.columns}
    st.markdown('<div class="sh">Харилцагчийн бүрэн өгөгдөл</div>', unsafe_allow_html=True)
    st.caption(f"Нийт **{len(df):,}** харилцагч · **{len(dcols)}** багана")

    show_od = st.checkbox("Зөвхөн хэтрэлттэй харилцагчийг харуулах", value=False)
    disp    = df[df["has_overdue"]] if show_od and "has_overdue" in df.columns else df

    sort_col = "MAX хэтрэлт (хоног)" if "MAX хэтрэлт (хоног)" in dcols.values() else list(dcols.values())[0]
    st.dataframe(
        disp[list(dcols.keys())].rename(columns=dcols)
            .sort_values(sort_col, ascending=False).reset_index(drop=True),
        use_container_width=True, height=520)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📥 Харилцагч CSV (бүх багана)",
            df.to_csv(index=False).encode("utf-8-sig"),
            f"customer_full_{selected}.csv", "text/csv", use_container_width=True)
    with col_dl2:
        od_only = df[df["has_overdue"]] if "has_overdue" in df.columns else df
        st.download_button(f"📥 Хэтэрсэн харилцагч CSV ({len(od_only):,})",
            od_only.to_csv(index=False).encode("utf-8-sig"),
            f"customer_overdue_{selected}.csv", "text/csv", use_container_width=True)
