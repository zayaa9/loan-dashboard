"""
export.py — Excel/CSV экспортын туслах функцүүд
"""
from io import BytesIO
import pandas as pd


def to_excel(dfs: dict[str, pd.DataFrame]) -> bytes:
    """Sheet тус бүрт DataFrame бүхий Excel файл үүсгэнэ."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for sheet, df in dfs.items():
            df.to_excel(w, sheet_name=sheet[:31], index=False)
    return buf.getvalue()
