import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ImportEntry:
    year: int
    source_type: str
    imported_at: str


def log_import(conn: sqlite3.Connection, year: int, source_type: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO import_log (year, source_type, imported_at) VALUES (?, ?, ?)",
        (year, source_type, now),
    )


def list_imports(conn: sqlite3.Connection) -> list[ImportEntry]:
    rows = conn.execute(
        "SELECT year, source_type, imported_at FROM import_log ORDER BY year DESC, source_type"
    ).fetchall()
    return [
        ImportEntry(
            year=int(row["year"]),
            source_type=str(row["source_type"]),
            imported_at=str(row["imported_at"]),
        )
        for row in rows
    ]


def has_b3_report(conn: sqlite3.Connection, year: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM import_log WHERE year = ? AND source_type = 'b3_report' LIMIT 1",
        (year,),
    ).fetchone()
    return row is not None


def has_movimentacao(conn: sqlite3.Connection, year: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM import_log WHERE year = ? AND source_type = 'movimentacao' LIMIT 1",
        (year,),
    ).fetchone()
    return row is not None
