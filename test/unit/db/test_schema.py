import sqlite3

from contabilidade.db.schema import CURRENT_VERSION, ensure_schema

_EXPECTED_TABLES = {
    "schema_version",
    "import_log",
    "acoes",
    "emprestimos",
    "etfs",
    "fundos",
    "renda_fixa",
    "tesouro_direto",
    "proventos",
    "reembolsos",
    "movimentacao",
}


def _memory_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def _user_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
    ).fetchall()
    return {row["name"] for row in rows}


def test_ensure_schema_creates_all_tables() -> None:
    conn = _memory_conn()
    ensure_schema(conn)
    assert _EXPECTED_TABLES == _user_tables(conn)


def test_ensure_schema_is_idempotent() -> None:
    conn = _memory_conn()
    ensure_schema(conn)
    ensure_schema(conn)  # Must not raise
    assert _EXPECTED_TABLES == _user_tables(conn)


def test_schema_version_is_set() -> None:
    conn = _memory_conn()
    ensure_schema(conn)
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    assert row is not None
    assert int(row["version"]) == CURRENT_VERSION
