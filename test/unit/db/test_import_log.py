import sqlite3

from contabilidade.db.import_log import (
    has_b3_report,
    has_movimentacao,
    list_imports,
    log_import,
)
from contabilidade.db.schema import ensure_schema


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def test_log_import_records_entry() -> None:
    conn = _conn()
    log_import(conn, 2024, "b3_report")
    entries = list_imports(conn)
    assert len(entries) == 1
    assert entries[0].year == 2024
    assert entries[0].source_type == "b3_report"
    assert entries[0].imported_at != ""


def test_list_imports_returns_all_entries_sorted() -> None:
    conn = _conn()
    log_import(conn, 2023, "b3_report")
    log_import(conn, 2024, "movimentacao")
    log_import(conn, 2024, "b3_report")
    entries = list_imports(conn)
    assert len(entries) == 3
    # ORDER BY year DESC, source_type → 2024/b3_report, 2024/movimentacao, 2023/b3_report
    assert entries[0].year == 2024
    assert entries[0].source_type == "b3_report"
    assert entries[1].year == 2024
    assert entries[1].source_type == "movimentacao"
    assert entries[2].year == 2023


def test_has_b3_report_returns_false_when_missing() -> None:
    conn = _conn()
    assert not has_b3_report(conn, 2024)


def test_has_b3_report_returns_true_after_import() -> None:
    conn = _conn()
    log_import(conn, 2024, "b3_report")
    assert has_b3_report(conn, 2024)
    assert not has_movimentacao(conn, 2024)
    log_import(conn, 2024, "movimentacao")
    assert has_movimentacao(conn, 2024)
