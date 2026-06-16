"""
tab_loan.py — 🏦 Данс түвшний таб (L1–L5)
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.archive import list_periods, load_period
from utils.charts import layout
from utils.config import (
    AXIS, BASE, CLR_BUCKET, CLR_STATUS,
    COL_AMT, COL_CUST, COL_DATE, COL_MAX_AOD,
    COL_MAX_OD, COL_SCORE, COL_STATUS1,
)


def render(df_acct: pd.DataFrame, df_cust: pd.DataFrame, selected: str) -> None:
    """Данс түвшний бүх дэд табыг дүрслэнэ."""

    # ── KPI тооцоо ────────────────────────────────────────────────────────────
    vc_all  = df_acct[COL_STATUS1].value_counts() if COL_STATUS1 in df_acct.columns else {}
    n_total = len(df_acct)
    n_C     = int(vc_all.get("C", 0))
    n_omax  = int(vc_all.get("O_max", 0))
    n_oact  = int(vc_all.get("O_active", 0))
    n_open  = n_omax + n_oact

    oa_d = (
        df_acct.loc[df_acct[COL_STATUS1] == "O_active", COL_MAX_AOD]
        if COL_STATUS1 in df_acct.columns and COL_MAX_AOD in df_acct.columns
        else pd.Series(dtype=float)
    )

    _n_cust      = df_acct[COL_CUST].nunique() if COL_CUST in df_acct.columns else 0
    _n_cust_C    = df_acct[df_acct[COL_STATUS1] == "C"][COL_CUST].nunique() if COL_STATUS1 in df_acct.columns and COL_CUST in df_acct.columns else 0
    _n_cust_open = df_acct[df_acct[COL_STATUS1].isin(["O_max","O_active"])][COL_CUST].nunique() if COL_STATUS1 in df_acct.columns and COL_CUST in df_acct.columns else 0
    _n_cust_oact = df_acct[df_acct[COL_STATUS1] == "O_active"][COL_CUST].nunique() if COL_STATUS1 in df_acct.columns and COL_CUST in df_acct.columns else 0

    # ── KPI эгнээ: Данс ──────────────────────────────────────────────────────
    st.markdown('<div style="font-size:12px;font-weight:600;color:#888;margin-bottom:4px;">📄 Дансны тоогоор</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Нийт данс",               f"{n_total:,}")
    k2.metric("🟢 Хаалттай (C)",          f"{n_C:,}",    f"{n_C/max(n_total,1)*100:.1f}%",    delta_color="off")
    k3.metric("🔵 Нээлттэй",              f"{n_open:,}", f"{n_open/max(n_total,1)*100:.1f}%",  delta_color="off")
    k4.metric("🔴 Идэвхтэй хэтрэлттэй",  f"{n_oact:,}", f"{n_oact/max(n_total,1)*100:.1f}%",  delta_color="off")
    k5.metric("30+ хоног",
        f"{int((oa_d>30).sum()):,}" if len(oa_d) else "–",
        f"{(oa_d>30).sum()/max(n_total,1)*100:.1f}%" if len(oa_d) else None,
        delta_color="off")
    k6.metric("Дундаж хэтрэлт",          f"{oa_d.mean():.1f} хон." if len(oa_d) else "–")

    # ── KPI эгнээ: Харилцагч ─────────────────────────────────────────────────
    st.markdown('<div style="font-size:12px;font-weight:600;color:#888;margin-bottom:4px;margin-top:8px;">👤 Харилцагчийн тоогоор</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Нийт харилцагч",           f"{_n_cust:,}")
    c2.metric("🟢 Хаалттай (C)",          f"{_n_cust_C:,}",    f"{_n_cust_C/max(_n_cust,1)*100:.1f}%",    delta_color="off")
    c3.metric("🔵 Нээлттэй",              f"{_n_cust_open:,}", f"{_n_cust_open/max(_n_cust,1)*100:.1f}%", delta_color="off")
    c4.metric("🔴 Идэвхтэй хэтрэлттэй",  f"{_n_cust_oact:,}", f"{_n_cust_oact/max(_n_cust,1)*100:.1f}%", delta_color="off")
    _oa_cust_od = (
        df_acct[df_acct[COL_STATUS1]=="O_active"].groupby(COL_CUST)[COL_MAX_AOD].max()
        if COL_STATUS1 in df_acct.columns and COL_CUST in df_acct.columns and COL_MAX_AOD in df_acct.columns
        else pd.Series(dtype=float)
    )
    c5.metric("30+ хоног",
        f"{int((_oa_cust_od>30).sum()):,}" if len(_oa_cust_od) else "–",
        f"{(_oa_cust_od>30).sum()/max(_n_cust,1)*100:.1f}%" if len(_oa_cust_od) else None,
        delta_color="off")
    c6.metric("Дундаж хэтрэлт", f"{_oa_cust_od.mean():.1f} хон." if len(_oa_cust_od) else "–")
    st.markdown("---")

    # ── Sub-tabs ──────────────────────────────────────────────────────────────
    L1, L2, L3, L4, L5 = st.tabs([
        "📋 Ерөнхий тойм",
        "⏱️ Хугацаа хэтрэлт",
        "🔍 Харилцагч хайх",
        "📅 Он сарын трэнд",
        "🗂️ Өгөгдөл",
    ])

    with L1:
        _render_overview(df_acct, n_total)
    with L2:
        _render_overdue(df_acct, n_total)
    with L3:
        _render_search(df_acct)
    with L4:
        _render_trend(selected)
    with L5:
        _render_data(df_acct, selected)


# ─────────────────────────────────────────────────────────────────────────────
# L1 — Ерөнхий тойм
# ─────────────────────────────────────────────────────────────────────────────
def _render_overview(df: pd.DataFrame, n_total: int) -> None:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="sh">Status_1 тархалт</div>', unsafe_allow_html=True)
        if COL_STATUS1 in df.columns:
            sv = df[COL_STATUS1].value_counts().reset_index()
            sv.columns = ["Төлөв","Тоо"]
            sv["Хувь"] = (sv["Тоо"]/sv["Тоо"].sum()*100).round(1)
            fig = px.bar(sv, x="Төлөв", y="Тоо", color="Төлөв",
                color_discrete_map=CLR_STATUS,
                text=sv.apply(lambda r: f"{r['Тоо']:,}\n({r['Хувь']}%)", axis=1))
            fig.update_traces(textposition="outside", textfont=dict(color="#111",size=12))
            layout(fig, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sh">Зээл олгосон он сараар — зээлийн төлөв</div>', unsafe_allow_html=True)
        if "loan_ym" in df.columns and COL_STATUS1 in df.columns:
            ym = pd.crosstab(df["loan_ym"], df[COL_STATUS1]).reset_index()
            ym = ym.melt(id_vars="loan_ym", var_name="Төлөв", value_name="Тоо")
            fig2 = px.bar(ym, x="loan_ym", y="Тоо", color="Төлөв",
                color_discrete_map=CLR_STATUS, barmode="stack")
            fig2.update_xaxes(tickangle=-40)
            layout(fig2, height=300)
            st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="sh">Зээлийн нийт дүн — зээлийн төлөв (box plot)</div>', unsafe_allow_html=True)
        if COL_AMT in df.columns and COL_STATUS1 in df.columns:
            fig3 = px.box(df, x=COL_STATUS1, y=COL_AMT,
                color=COL_STATUS1, color_discrete_map=CLR_STATUS)
            layout(fig3, height=280, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown('<div class="sh">Нэг харилцагчид ногдох зээлийн тоо</div>', unsafe_allow_html=True)
        if COL_CUST in df.columns and COL_STATUS1 in df.columns:
            lc = df.groupby(COL_CUST).size().reset_index(name="Зээлийн тоо")
            oa_cnt = (df[df[COL_STATUS1]=="O_active"]
                      .groupby(COL_CUST).size().reset_index(name="OA"))
            lc = lc.merge(oa_cnt, on=COL_CUST, how="left")
            lc["OA"] = lc["OA"].fillna(0).astype(int)
            grp = lc.groupby("Зээлийн тоо").agg(
                Харилцагч    =("Зээлийн тоо", "count"),
                OA_харилцагч =("OA", lambda x: (x>0).sum()),
            ).reset_index()
            grp = grp[grp["Харилцагч"] >= 3].copy()
            grp["OA_%"] = (grp["OA_харилцагч"]/grp["Харилцагч"]*100).round(1)

            fig4 = go.Figure()
            fig4.add_trace(go.Bar(
                x=grp["Зээлийн тоо"], y=grp["Харилцагч"],
                name="Нийт харилцагч",
                marker=dict(color="#1a73e8", opacity=0.8, line=dict(width=0)),
                width=0.7, yaxis="y1",
            ))
            fig4.add_trace(go.Bar(
                x=grp["Зээлийн тоо"], y=grp["OA_харилцагч"],
                name="Идэвхтэй хэтрэлттэй",
                marker=dict(color="#e24b4a", opacity=0.85, line=dict(width=0)),
                width=0.7, yaxis="y1",
            ))
            fig4.add_trace(go.Scatter(
                x=grp["Зээлийн тоо"], y=grp["OA_%"],
                name="Хэтрэлтийн %",
                mode="lines+markers",
                line=dict(color="#f59e0b", width=2.5),
                marker=dict(size=8, color="#f59e0b", line=dict(color="#fff", width=1.5)),
                yaxis="y2",
            ))
            layout(fig4, height=340,
                barmode="overlay",
                xaxis=dict(**AXIS,
                    title="Зээлийн тоо (нэг харилцагчид)",
                    tickmode="array",
                    tickvals=grp["Зээлийн тоо"].tolist(),
                    ticktext=[str(v) for v in grp["Зээлийн тоо"].tolist()],
                ),
                yaxis=dict(**AXIS, title="Харилцагчийн тоо"),
                yaxis2=dict(
                    overlaying="y", side="right",
                    title="Хэтрэлтийн %", ticksuffix="%",
                    tickfont=dict(color="#f59e0b",size=11),
                    title_font=dict(color="#f59e0b",size=12),
                    gridcolor="rgba(0,0,0,0)",
                    range=[0, min(grp["OA_%"].max()*2.5, 100)],
                ),
                legend=dict(font=dict(color="#111",size=11), bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#ddd", borderwidth=1, x=0.99, xanchor="right", y=0.99, yanchor="top"),
                margin=dict(l=10, r=70, t=32, b=8),
            )
            st.plotly_chart(fig4, use_container_width=True)

    # Нэгтгэл хүснэгт
    st.markdown('<div class="sh">Зээлийн төлвөөр нэгтгэсэн хүснэгт</div>', unsafe_allow_html=True)
    rows = []
    for s in ["C","O_max","O_active"]:
        sub = df[df[COL_STATUS1]==s] if COL_STATUS1 in df.columns else pd.DataFrame()
        row = {"Төлөв": s, "Данс": len(sub), "Хувь (%)": round(len(sub)/max(n_total,1)*100, 1)}
        if COL_AMT in sub.columns:
            row["Нийт дүн (₮)"] = sub[COL_AMT].sum()
            row["Дундаж дүн"]   = round(sub[COL_AMT].mean(), 0)
        if COL_MAX_AOD in sub.columns:
            row["Дундаж хэтрэлт"] = round(sub[COL_MAX_AOD].mean(), 1)
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# L2 — Хугацаа хэтрэлт
# ─────────────────────────────────────────────────────────────────────────────
def _render_overdue(df: pd.DataFrame, n_total: int) -> None:
    oa   = df[df[COL_STATUS1]=="O_active"].copy() if COL_STATUS1 in df.columns else df.copy()
    _oad = oa[COL_MAX_AOD] if COL_MAX_AOD in oa.columns else pd.Series(dtype=float)

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Идэвхтэй х.хэтэрсэн данс", f"{len(oa):,}")
    b2.metric("Дундаж хэтрэлт",   f"{_oad.mean():.1f} хон." if len(_oad) else "–")
    b3.metric("Медиан",            f"{_oad.median():.0f} хон." if len(_oad) else "–")
    b4.metric("Хамгийн их",        f"{int(_oad.max())} хон." if len(_oad) else "–")

    bk1 = st.columns(6)
    for i, (lbl, lo, hi) in enumerate([
        ("1 хоног",1,1),("2–5",2,5),("6–10",6,10),("11–15",11,15),("16–30",16,30),("30+",31,9999)
    ]):
        _n = int(_oad.between(lo,hi).sum()) if len(_oad) else 0
        bk1[i].metric(lbl, f"{_n:,}", f"{_n/max(n_total,1)*100:.1f}%", delta_color="off")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sh">Хэтрэлтийн хоногийн тархалт</div>', unsafe_allow_html=True)
        if len(_oad):
            fig = px.histogram(oa, x=COL_MAX_AOD, nbins=31, color_discrete_sequence=["#e24b4a"])
            fig.add_vline(x=30, line_dash="dash", line_color="#888", annotation_text="30 хоног")
            layout(fig, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sh">Эрсдэлийн оноо × Хугацаа хэтрэлт (scatter)</div>', unsafe_allow_html=True)
        if COL_SCORE in oa.columns and COL_MAX_AOD in oa.columns:
            fig2 = px.scatter(oa, x=COL_SCORE, y=COL_MAX_AOD,
                color="bucket" if "bucket" in oa.columns else None,
                color_discrete_sequence=CLR_BUCKET,
                opacity=0.55, trendline="ols",
                labels={COL_SCORE:"Эрсдэлийн оноо", COL_MAX_AOD:"Идэвхтэй хэтрэлт (хоног)", "bucket":"Хэтрэлтийн бүс"})
            corr = oa[[COL_SCORE,COL_MAX_AOD]].dropna().corr().iloc[0,1]
            layout(fig2, height=300)
            st.plotly_chart(fig2, use_container_width=True)
            if corr > 0.1:
                msg = "Оноо өндөр байсан ч хугацаа хэтрэлт ихэссэн хандлага ажиглагдаж байна."
            elif corr < -0.1:
                msg = "Оноо бага байсан харилцагчид илүү их хэтэрч байна — оноолтын загвар зөв таньж байна."
            else:
                msg = "Оноо болон хэтрэлтийн хоорондын хамаарал маш сул байна."
            st.caption(f"Корреляц: **{corr:+.3f}** — {msg}")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="sh">Оноогийн бүсээр — O_active тоо & rate</div>', unsafe_allow_html=True)
        if "score_band" in oa.columns and "score_band" in df.columns:
            sb_oa  = oa["score_band"].value_counts().sort_index().reset_index()
            sb_oa.columns = ["Бүс","O_active тоо"]
            sb_all = df["score_band"].value_counts().sort_index().reset_index()
            sb_all.columns = ["Бүс","Нийт"]
            sb = sb_oa.merge(sb_all, on="Бүс", how="left")
            sb["Rate %"] = (sb["O_active тоо"]/sb["Нийт"]*100).round(1)

            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=sb["Бүс"].astype(str), y=sb["O_active тоо"],
                name="O_active тоо",
                marker=dict(color=sb["O_active тоо"],
                    colorscale=[[0,"#aac8f5"],[1,"#e24b4a"]], showscale=False),
                yaxis="y1",
            ))
            fig3.add_trace(go.Scatter(
                x=sb["Бүс"].astype(str), y=sb["Rate %"],
                name="O_active rate %",
                mode="lines+markers+text",
                line=dict(color="#e24b4a",width=2.5),
                marker=dict(size=8, color="#e24b4a", line=dict(color="#fff",width=1.5)),
                text=sb["Rate %"].astype(str)+"%",
                textposition="top center", textfont=dict(color="#e24b4a",size=11),
                yaxis="y2",
            ))
            layout(fig3, height=300,
                xaxis=dict(**AXIS, title="Оноогийн бүс", tickangle=-20),
                yaxis=dict(**AXIS, title="O_active дансны тоо"),
                yaxis2=dict(overlaying="y", side="right", title="O_active rate %",
                    ticksuffix="%", tickfont=dict(color="#e24b4a",size=11),
                    title_font=dict(color="#e24b4a",size=12),
                    gridcolor="rgba(0,0,0,0)",
                    range=[0, min(sb["Rate %"].max()*2.5, 100)]),
                legend=dict(font=dict(color="#111",size=11), bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#ddd", borderwidth=1, x=0.99, xanchor="right", y=0.99, yanchor="top"),
                margin=dict(l=10, r=70, t=32, b=8),
            )
            st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown('<div class="sh">Нийт хэтрэлт vs Идэвхтэй хэтрэлт</div>', unsafe_allow_html=True)
        if COL_MAX_OD in oa.columns and COL_MAX_AOD in oa.columns:
            fig4 = go.Figure()
            fig4.add_trace(go.Histogram(x=oa[COL_MAX_OD], name="Нийт (max_overdue)",
                opacity=0.5, marker_color="#f59e0b", nbinsx=31))
            fig4.add_trace(go.Histogram(x=oa[COL_MAX_AOD], name="Идэвхтэй",
                opacity=0.7, marker_color="#e24b4a", nbinsx=31))
            layout(fig4, height=280, barmode="overlay")
            st.plotly_chart(fig4, use_container_width=True)

    # Яаралтай жагсаалт
    st.markdown("---")
    thr  = st.slider("Яаралтай жагсаалт — хязгаар (хоног)", 20, 31, 25, key="thr_loan")
    oa25 = oa[oa[COL_MAX_AOD] >= thr] if COL_MAX_AOD in oa.columns else pd.DataFrame()
    if len(oa25):
        st.markdown(
            f'<div class="box box-danger">🚨 <b>{thr}+</b> хоног: <b>{len(oa25):,}</b> данс ({len(oa25)/max(len(oa),1)*100:.1f}%)</div>',
            unsafe_allow_html=True)
        show = {k:v for k,v in {
            COL_CUST:"Харилцагч", COL_DATE:"Огноо",
            COL_AMT:"Дүн", COL_MAX_AOD:"Хэтрэлт", COL_SCORE:"Оноо",
        }.items() if k in oa25.columns}
        st.dataframe(
            oa25[list(show.keys())].rename(columns=show)
                .sort_values("Хэтрэлт", ascending=False).reset_index(drop=True),
            use_container_width=True, height=320)
        st.download_button("📥 Татах", oa25.to_csv(index=False).encode("utf-8-sig"),
            f"urgent_{thr}plus.csv", "text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# L3 — Харилцагч хайх
# ─────────────────────────────────────────────────────────────────────────────
def _render_search(df: pd.DataFrame) -> None:
    if COL_CUST not in df.columns:
        st.warning(f"'{COL_CUST}' багана байхгүй.")
        return

    # Dropdown label үүсгэнэ — бүрэн векторжуулсан (iterrows / groupby.apply ашиглахгүй → ~40x хурдан)
    if COL_STATUS1 in df.columns:
        prec = df[COL_STATUS1].map({"O_active": 2, "O_max": 1}).fillna(0).astype("int8")
        d    = df.assign(_prec=prec)
        info = d.groupby(COL_CUST).agg(
            loan_cnt=(COL_CUST, "count"),
            max_od  =(COL_MAX_AOD, "max"),
            _p      =("_prec", "max"),
        ).reset_index()
        info["has_oa"] = info["_p"].map({2: "🔴", 1: "🟡", 0: "🟢"})
    else:
        info = df.groupby(COL_CUST).agg(
            loan_cnt=(COL_CUST, "count"),
            max_od  =(COL_MAX_AOD, "max"),
        ).reset_index()
        info["has_oa"] = "–"

    info = info.sort_values(["loan_cnt", "max_od"], ascending=[False, False]).reset_index(drop=True)

    _od_str = np.where(
        info["max_od"] > 0,
        " | MAX:" + info["max_od"].fillna(0).astype(int).astype(str) + "хон",
        "",
    )
    info["label"] = (
        info[COL_CUST].astype(str) + "  —  "
        + info["loan_cnt"].astype(int).astype(str) + " зээл  "
        + info["has_oa"].astype(str) + _od_str
    )
    labels   = info["label"].tolist()
    code_map = dict(zip(info["label"], info[COL_CUST].astype(str)))

    if not labels:
        st.warning("Харилцагч олдсонгүй.")
        return

    col_sel, col_info = st.columns([3,1])
    with col_sel:
        chosen_lbl = st.selectbox(
            f"Харилцагч сонгох ({len(labels):,} харилцагч):",
            options=labels, index=0,
        )
    with col_info:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"Нийт **{len(labels):,}** харилцагч")

    selected_code = code_map.get(chosen_lbl, "")
    rows_ = df[df[COL_CUST].astype(str).str.strip() == selected_code]

    if rows_.empty:
        st.warning("Олдсонгүй.")
        return

    vc2 = rows_[COL_STATUS1].value_counts() if COL_STATUS1 in rows_.columns else {}
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Нийт зээл",    len(rows_))
    c2.metric("C",            int(vc2.get("C",0)))
    c3.metric("O_max",        int(vc2.get("O_max",0)))
    c4.metric("O_active",     int(vc2.get("O_active",0)))
    c5.metric("MAX хэтрэлт",  f"{int(rows_[COL_MAX_AOD].max())} хон." if COL_MAX_AOD in rows_.columns else "–")

    show = {k:v for k,v in {
        COL_DATE:"Огноо", COL_AMT:"Дүн",
        COL_STATUS1:"Төлөв", COL_SCORE:"Оноо",
        COL_MAX_AOD:"Идэвхтэй хэтрэлт", "bucket":"Bucket",
    }.items() if k in rows_.columns}
    st.dataframe(
        rows_[list(show.keys())].rename(columns=show)
            .sort_values("Огноо" if "Огноо" in show.values() else list(show.values())[0])
            .reset_index(drop=True),
        use_container_width=True, height=280)

    if COL_DATE in rows_.columns and COL_MAX_AOD in rows_.columns:
        rs = rows_.sort_values(COL_DATE).copy()
        rs["lbl"] = rs[COL_DATE].dt.strftime("%Y-%m-%d")
        fig = px.bar(rs, x="lbl", y=COL_MAX_AOD,
            color=COL_STATUS1 if COL_STATUS1 in rs.columns else None,
            color_discrete_map=CLR_STATUS, text=COL_MAX_AOD,
            labels={"lbl":"Авсан огноо", COL_MAX_AOD:"Хэтрэлт (хоног)"})
        fig.add_hline(y=25, line_dash="dash", line_color="#888",
            annotation_text="25 хоног", annotation_font=dict(color="#888",size=11))
        fig.update_traces(textposition="outside", textfont=dict(color="#111",size=12))
        layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# L4 — Он сарын трэнд
# ─────────────────────────────────────────────────────────────────────────────
def _render_trend(selected: str) -> None:
    all_p = list_periods()
    if len(all_p) < 2:
        st.info("2+ үе хадгалагдсан байх шаардлагатай.")
        return

    rows = []
    for p in reversed(all_p):
        try:
            dp = load_period(p)
            s1 = dp[COL_STATUS1].value_counts() if COL_STATUS1 in dp.columns else {}
            n  = len(dp)
            oad = dp.loc[dp[COL_STATUS1]=="O_active", COL_MAX_AOD] if COL_STATUS1 in dp.columns and COL_MAX_AOD in dp.columns else pd.Series()
            rows.append({
                "Он сар": p, "Нийт данс": n,
                "C": int(s1.get("C",0)), "O_max": int(s1.get("O_max",0)),
                "O_active": int(s1.get("O_active",0)),
                "O_active %": round(s1.get("O_active",0)/max(n,1)*100, 1),
                "Дундаж хэтрэлт": round(oad.mean(),2) if len(oad) else 0,
            })
        except Exception:
            pass
    tdf = pd.DataFrame(rows)

    if len(tdf) >= 2:
        cur, prev = tdf.iloc[-1], tdf.iloc[-2]
        d1, d2, d3 = st.columns(3)
        d1.metric("Энэ үеийн O_active", f"{cur['O_active']:,}")
        d2.metric("Өмнөх үетэй зөрүү",  f"{cur['O_active']-prev['O_active']:+,}", delta_color="inverse")
        d3.metric("O_active % зөрүү",    f"{cur['O_active %']-prev['O_active %']:+.1f}%", delta_color="inverse")
        st.markdown("---")

        fig = go.Figure()
        fig.add_trace(go.Bar(x=tdf["Он сар"], y=tdf["O_active"],
            name="O_active тоо", marker_color="rgba(226,75,74,.2)", yaxis="y2"))
        fig.add_trace(go.Scatter(x=tdf["Он сар"], y=tdf["O_active %"],
            name="O_active %", mode="lines+markers+text",
            line=dict(color="#e24b4a",width=2.5), marker=dict(size=9),
            text=tdf["O_active %"].astype(str)+"%",
            textposition="top center", textfont=dict(color="#e24b4a",size=11)))
        layout(fig, height=360,
            yaxis=dict(**AXIS, title="O_active %"),
            yaxis2=dict(overlaying="y", side="right", title="Тоо",
                        tickfont=dict(color="#bbb",size=10), gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(tdf, use_container_width=True, height=240)
    st.download_button("📥 Трэнд татах", tdf.to_csv(index=False).encode("utf-8-sig"),
        "trend.csv", "text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# L5 — Өгөгдөл
# ─────────────────────────────────────────────────────────────────────────────
def _render_data(df: pd.DataFrame, selected: str) -> None:
    quick  = st.radio("", ["Бүгд","O_active","O_max","C"], horizontal=True)
    show_  = df[df[COL_STATUS1]==quick].copy() if quick != "Бүгд" and COL_STATUS1 in df.columns else df.copy()
    st.caption(f"{len(show_):,} данс")
    dcols  = {k:v for k,v in {
        COL_CUST:"Харилцагч", COL_DATE:"Огноо",
        COL_AMT:"Дүн", COL_STATUS1:"Төлөв", COL_SCORE:"Оноо",
        COL_MAX_AOD:"Хэтрэлт", "bucket":"Bucket",
    }.items() if k in show_.columns}
    sort_c = "Хэтрэлт" if "Хэтрэлт" in dcols.values() else list(dcols.values())[0]
    st.dataframe(
        show_[list(dcols.keys())].rename(columns=dcols)
            .sort_values(sort_c, ascending=False).reset_index(drop=True),
        use_container_width=True, height=500)
    st.download_button("📥 CSV татах", show_.to_csv(index=False).encode("utf-8-sig"),
        f"loan_{quick}_{selected}.csv", "text/csv")
