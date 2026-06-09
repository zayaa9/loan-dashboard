"""
archive.py — Архив хадгалах, уншах, устгах функцүүд
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ARCHIVE_DIR = Path("archive")
ARCHIVE_DIR.mkdir(exist_ok=True)


def _ap(period: str) -> Path:
    return ARCHIVE_DIR / f"{period}.parquet"


def _mp(period: str) -> Path:
    return ARCHIVE_DIR / f"{period}.json"


def list_periods() -> list[str]:
    """Хадгалагдсан бүх үеийн жагсаалт (шинэ→хуучин)."""
    return [f.stem for f in sorted(ARCHIVE_DIR.glob("*.parquet"), reverse=True)]


def save_period(df: pd.DataFrame, period: str, filename: str = "") -> None:
    """DataFrame-ийг parquet болгон хадгална."""
    df.to_parquet(_ap(period), index=False)
    _mp(period).write_text(
        json.dumps(
            {
                "filename": filename,
                "saved_at": datetime.now().isoformat(),
                "rows": len(df),
            },
            ensure_ascii=False,
        )
    )


def load_meta(period: str) -> dict:
    """Тухайн үеийн мета мэдээлэл (filename, rows, saved_at)."""
    p = _mp(period)
    return json.loads(p.read_text()) if p.exists() else {}


def load_period(period: str) -> pd.DataFrame:
    """Parquet файлыг уншиж DataFrame буцаана."""
    df = pd.read_parquet(_ap(period))
    df.columns = df.columns.str.strip().str.lower()
    return df


def delete_period(period: str) -> None:
    """Тухайн үеийн parquet + json файлыг устгана."""
    for f in [_ap(period), _mp(period)]:
        if f.exists():
            f.unlink()
