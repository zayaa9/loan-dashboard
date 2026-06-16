# -*- coding: utf-8 -*-
"""
report_cowork.py — ETL-ийн эцсийн датанд үндэслэн Word тайлан үүсгэнэ.
=====================================================================
ЧУХАЛ: Энэ скрипт түүхий CSV-г УНШИХГҮЙ.
Харин etl_cowork.py-ийн гаргасан ЭЦСИЙН датаг (archive/*.parquet) уншина.
Тиймээс run_loan_etl.bat дотор ЗААВАЛ etl_cowork.py-ийн ДАРАА ажиллана.

Урсгал:
    etl_cowork.py  →  archive/2026-06-15.parquet  →  report_cowork.py  →  reports/loan_report_2026-06-15.docx

Шаардлагатай сан:
    pip install pandas matplotlib python-docx pyarrow

Ажиллуулах:
    py report_cowork.py
"""

import os
import io
import glob
import datetime as dt
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ======================================================================
# ТОХИРГОО
# ======================================================================
BASE_DIR = Path(__file__).parent              # энэ скрипттэй ижил хавтас
ARCHIVE_DIR = BASE_DIR / "archive"            # ETL-ийн эцсийн parquet энд байна
OUTPUT_DIR = BASE_DIR / "reports"             # тайлан энд хадгалагдана

STREAMLIT_URL = "https://loan-dashboardgit-jht3b94lsjnllhvcdu7swo.streamlit.app/"       # <-- дашбордын линкээ бичнэ
REPORT_TITLE = "Зээлийн эрсдэл — долоо хоног тутмын тайлан"

# Streamlit Cloud дашбордруу upload хийх файлуудыг хураах хавтас
# (CSV utf-8-sig — монгол үсэг гажихгүй, найдвартай, огноотойгоор хураана)
UPLOAD_DIR = BASE_DIR / "dashboard_uploads"

# Хэтрэлтийн бүс (config.py-тай ижил дараалал ба өнгө)
BUCKET_ORDER = ["0", "1", "2–5", "6–10", "11–15", "16–30", "30+"]
BUCKET_COLORS = {
    "0": "#1d9e75", "1": "#84cc16", "2–5": "#f59e0b", "6–10": "#f97316",
    "11–15": "#ef4444", "16–30": "#dc2626", "30+": "#7f1d1d",
}
STATUS_LABELS = {"O_active": "Идэвхтэй хэтрэлт", "O_max": "Хэтэрсэн (хаагдсан)", "C": "Хэвийн (хаалттай)"}
STATUS_COLORS = {"O_active": "#e24b4a", "O_max": "#f59e0b", "C": "#1d9e75"}
# ======================================================================


def money(x) -> str:
    """Мөнгөн дүнг таслалтай форматлана (₮)."""
    try:
        return f"{float(x):,.0f} ₮"
    except (TypeError, ValueError):
        return "—"


def load_final_data():
    """archive/ доторх ХАМГИЙН СҮҮЛИЙН parquet-ийг (ETL-ийн эцсийн дата) уншина."""
    files = glob.glob(str(ARCHIVE_DIR / "*.parquet"))
    if not files:
        raise FileNotFoundError(
            f"{ARCHIVE_DIR} дотроос parquet олдсонгүй. "
            f"Эхлээд etl_cowork.py-г ажиллуулсан эсэхээ шалгана уу."
        )
    path = max(files, key=os.path.getmtime)
    df = pd.read_parquet(path)
    print(f"Эцсийн дата уншлаа: {os.path.basename(path)}  ({len(df):,} мөр)")
    return df, os.path.basename(path)


def compute_kpis(df: pd.DataFrame) -> dict:
    """Дашбордын гол үзүүлэлтүүдийг тооцоолно."""
    k = {"Нийт зээлийн данс": f"{len(df):,}"}
    if "adv_amt" in df.columns:
        k["Нийт олгосон дүн"] = money(df["adv_amt"].sum())
        k["Дундаж зээлийн дүн"] = money(df["adv_amt"].mean())
    if "total_score" in df.columns:
        k["Дундаж нийт оноо"] = f"{df['total_score'].mean():.0f}"
    if "is_overdue" in df.columns:
        n = int(df["is_overdue"].sum())
        k["Хэтэрсэн зээл (нийт)"] = f"{n:,}  ({n/len(df)*100:.1f}%)"
    if "active_overdue" in df.columns:
        n = int(df["active_overdue"].sum())
        k["Идэвхтэй хэтрэлттэй"] = f"{n:,}  ({n/len(df)*100:.1f}%)"
    if "max_active_overdue_day" in df.columns:
        k["Дундаж идэвхтэй хэтрэлт (хоног)"] = f"{df['max_active_overdue_day'].mean():.1f}"
    return k


def _bar(series, title, colors=None, xlabel=""):
    """График зурж, санах ой доторх PNG (BytesIO)-г буцаана. Файл хадгалахгүй."""
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(series.index.astype(str), series.values)
    if colors:
        for b, lbl in zip(bars, series.index.astype(str)):
            b.set_color(colors.get(lbl, "#2563eb"))
    else:
        for b in bars:
            b.set_color("#2563eb")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    for b in bars:
        ax.annotate(f"{int(b.get_height()):,}", (b.get_x() + b.get_width()/2, b.get_height()),
                    ha="center", va="bottom", fontsize=8)
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def make_charts(df: pd.DataFrame) -> list:
    """Хэтрэлтийн бүс, төлөв, оноо, байршлаар график зурж, санах ойд үүсгэнэ."""
    charts = []  # (BytesIO, тайлбар)

    # 1. Хэтрэлтийн бүс (bucket)
    if "bucket" in df.columns:
        s = df["bucket"].value_counts().reindex(BUCKET_ORDER).dropna()
        buf = _bar(s, "Хэтрэлтийн бүс (хоногоор) — дансны тоо", BUCKET_COLORS, "Хэтрэлтийн бүс")
        charts.append((buf, "Идэвхтэй хэтрэлтийн хоногийн бүс тус бүрийн дансны тоо."))

    # 2. Төлөв (status_1)
    if "status_1" in df.columns:
        s = df["status_1"].value_counts()
        s.index = [STATUS_LABELS.get(i, i) for i in s.index]
        cmap = {STATUS_LABELS.get(k, k): v for k, v in STATUS_COLORS.items()}
        buf = _bar(s, "Зээлийн төлвийн ангилал", cmap)
        charts.append((buf, "Зээлийн төлвөөр (идэвхтэй хэтрэлт / хэтэрсэн / хэвийн) ангилсан тоо."))

    # 3. Онооны бүс (score_band)
    if "score_band" in df.columns:
        order = ["<350", "351–400", "401–450", "451–500", "501–550", "551+"]
        s = df["score_band"].value_counts().reindex(order).dropna()
        buf = _bar(s, "Онооны бүсээр хуваарилалт", None, "Онооны бүс")
        charts.append((buf, "Нийт оноогоор бүлэглэсэн дансны тархалт."))

    # 4. Хэтрэлтийн хувь — байршлаар
    if {"location_type", "is_overdue"}.issubset(df.columns):
        s = (df.groupby("location_type")["is_overdue"].mean() * 100).round(1)
        buf = _bar(s, "Хэтрэлтийн хувь — байршлаар (%)", None, "Байршил")
        charts.append((buf, "Улаанбаатар ба орон нутгийн хэтэрсэн зээлийн эзлэх хувь."))

    return charts


def _add_table(doc, series, col1, col2):
    """value_counts маягийн Series-г 2 баганатай хүснэгт болгоно."""
    t = doc.add_table(rows=1, cols=2)
    t.style = "Light Grid Accent 1"
    t.rows[0].cells[0].text = col1
    t.rows[0].cells[1].text = col2
    total = series.sum()
    for idx, val in series.items():
        c = t.add_row().cells
        c[0].text = str(idx)
        c[1].text = f"{int(val):,}  ({val/total*100:.1f}%)"


def build_report(df, kpis, charts, src_name, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().strftime("%Y-%m-%d")
    doc = Document()

    h = doc.add_heading(REPORT_TITLE, level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(f"Тайлангийн огноо: {today}   ·   Эх дата: {src_name}")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    p.add_run("Дашборд (онлайн): ").bold = True
    p.add_run(STREAMLIT_URL)

    doc.add_heading("Тойм", level=1)
    doc.add_paragraph(
        f"Энэхүү тайланг ETL-ийн боловсруулсан эцсийн датанд ({src_name}) "
        f"үндэслэн {today}-нд автоматаар үүсгэв. Доорх үзүүлэлтүүд нь "
        f"overdue болон features файлуудыг нэгтгэж, цэвэрлэсний дараах "
        f"эцсийн дүн юм. Дэлгэрэнгүйг дээрх дашбордын линкээр үзнэ үү."
    )

    doc.add_heading("Гол үзүүлэлтүүд", level=1)
    kt = doc.add_table(rows=0, cols=2)
    kt.style = "Light Grid Accent 1"
    for key, val in kpis.items():
        c = kt.add_row().cells
        c[0].text = key
        c[1].text = str(val)
        c[0].paragraphs[0].runs[0].bold = True if c[0].paragraphs[0].runs else None

    if "bucket" in df.columns:
        doc.add_heading("Хэтрэлтийн бүсээр", level=1)
        s = df["bucket"].value_counts().reindex(BUCKET_ORDER).dropna()
        _add_table(doc, s, "Хэтрэлтийн бүс (хоног)", "Дансны тоо")

    if "status_1" in df.columns:
        doc.add_heading("Төлвийн ангилалаар", level=1)
        s = df["status_1"].value_counts()
        s.index = [STATUS_LABELS.get(i, i) for i in s.index]
        _add_table(doc, s, "Төлөв", "Дансны тоо")

    if charts:
        doc.add_heading("Графикууд", level=1)
        for buf, caption in charts:
            doc.add_picture(buf, width=Inches(6))
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in cap.runs:
                run.italic = True
                run.font.size = Pt(9)

    out_path = outdir / f"loan_report_{today}.docx"
    doc.save(str(out_path))
    return out_path


def export_for_dashboard(df: pd.DataFrame) -> Path:
    """Эцсийн датаг Streamlit Cloud дашбордруу upload хийх CSV болгож,
    dashboard_uploads/ хавтаст огноотойгоор хадгална.
    utf-8-sig кодчилол → Excel болон дашбордод монгол үсэг зөв харагдана."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().strftime("%Y-%m-%d")
    out = UPLOAD_DIR / f"dashboard_upload_{today}.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Дашбордын upload файл хадгалагдлаа: {out.name}")
    return out


def main():
    df, src = load_final_data()
    kpis = compute_kpis(df)
    charts = make_charts(df)
    report = build_report(df, kpis, charts, src, OUTPUT_DIR)
    print(f"Тайлан амжилттай хадгалагдлаа: {report}")
    export_for_dashboard(df)


if __name__ == "__main__":
    main()
