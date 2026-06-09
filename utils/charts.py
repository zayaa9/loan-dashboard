"""
charts.py — Plotly layout helper болон давтагдах chart функцүүд
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.config import AXIS, BASE, LEGEND, CLR_STATUS, CLR_BUCKET


def layout(fig: go.Figure, **kw) -> go.Figure:
    """BASE layout дээр нэмэлт параметр merge хийж тохируулна."""
    fig.update_layout(**{**BASE, **kw})
    fig.update_xaxes(**AXIS)
    fig.update_yaxes(**AXIS)
    return fig


def dual_bar_rate(
    df: pd.DataFrame,
    x_col: str,
    y_avg_col: str,
    y_rate_col: str,
    n_col: str,
    title_left: str = "Дундаж хоног",
    title_right: str = "Хэтрэлтийн rate %",
    height: int = 300,
    min_cnt: int = 3,
) -> go.Figure | None:
    """
    Dual-axis chart:
      - Bar:    дундаж утга (зүүн тэнхлэг)
      - Line:   хэтрэлтийн rate % (баруун тэнхлэг)
    """
    d = df[df[n_col] >= min_cnt].copy()
    if d.empty:
        return None

    cats = d[x_col].astype(str).tolist()

    bar_max = d[y_avg_col].max()
    bar_colors = [
        f"rgba({int(26 + (226-26)*v)},{int(115 + (75-115)*v)},{int(232 + (74-232)*v)},0.82)"
        for v in [x / max(bar_max, 1) for x in d[y_avg_col]]
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cats, y=d[y_avg_col],
        name=title_left,
        marker_color=bar_colors,
        text=d[y_avg_col].round(1),
        textposition="outside",
        textfont=dict(color="#111", size=11),
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=cats, y=d[y_rate_col],
        name=title_right,
        mode="lines+markers+text",
        line=dict(color="#e24b4a", width=2.5),
        marker=dict(size=8, color="#e24b4a", line=dict(color="#fff", width=1.5)),
        text=d[y_rate_col].astype(str) + "%",
        textposition="top center",
        textfont=dict(color="#e24b4a", size=11),
        yaxis="y2",
    ))

    layout(
        fig, height=height,
        xaxis=dict(**{**AXIS, "tickfont": dict(color="#111", size=11)},
                   tickangle=-30, automargin=True),
        yaxis=dict(**AXIS, title=title_left),
        yaxis2=dict(
            overlaying="y", side="right",
            title=title_right,
            ticksuffix="%",
            tickfont=dict(color="#e24b4a", size=11),
            title_font=dict(color="#e24b4a", size=12),
            gridcolor="rgba(0,0,0,0)",
            range=[0, min(d[y_rate_col].max() * 2, 100)],
        ),
        legend=dict(
            font=dict(color="#111", size=11),
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#ddd", borderwidth=1,
            orientation="v",
            x=0.01, xanchor="left",
            y=0.99, yanchor="top",
        ),
        barmode="group",
        margin=dict(l=10, r=20, t=36, b=8),
    )
    return fig


def corr_box(corr: float, pos_msg: str, neg_msg: str, neutral_msg: str) -> tuple[str, str]:
    """Корреляцын утгаас тайлбар текст болон CSS class буцаана."""
    if corr < -0.05:
        return neg_msg, "box box-green"
    elif corr > 0.05:
        return pos_msg, "box box-warn"
    else:
        return neutral_msg, "box box-blue"
