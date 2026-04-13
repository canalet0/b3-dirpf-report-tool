import sqlite3
from decimal import Decimal

from contabilidade.db.movimentacao_repository import (
    load_movimentacao_report,
    save_movimentacao_report,
)
from contabilidade.db.schema import ensure_schema
from contabilidade.models.movimentacao import MovimentacaoReport, MovimentacaoRow


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def _make_report(year: int = 2024) -> MovimentacaoReport:
    return MovimentacaoReport(
        year=year,
        rows=[
            MovimentacaoRow(
                entrada_saida="Credito",
                data="27/11/2024",
                movimentacao="Dividendo",
                produto="TAEE11 - TAESA",
                instituicao="INTER",
                quantidade=Decimal("34"),
                preco_unitario=Decimal("0.305"),
                valor_operacao=Decimal("10.37"),
            ),
            MovimentacaoRow(
                entrada_saida="Debito",
                data="23/12/2024",
                movimentacao="Transferência - Liquidação",
                produto="WEGE3 - WEG S.A.",
                instituicao="INTER",
                quantidade=Decimal("28"),
                preco_unitario=None,
                valor_operacao=None,
            ),
        ],
    )


def test_save_and_load_movimentacao_roundtrip() -> None:
    conn = _conn()
    original = _make_report(2024)
    save_movimentacao_report(conn, original)
    loaded = load_movimentacao_report(conn, 2024)
    assert loaded is not None
    assert loaded.year == original.year
    assert loaded.rows == original.rows


def test_none_decimal_fields_stored_as_null_and_loaded_as_none() -> None:
    conn = _conn()
    save_movimentacao_report(conn, _make_report(2024))
    loaded = load_movimentacao_report(conn, 2024)
    assert loaded is not None
    sell_row = loaded.rows[1]
    assert sell_row.preco_unitario is None
    assert sell_row.valor_operacao is None
    buy_row = loaded.rows[0]
    assert buy_row.preco_unitario == Decimal("0.305")
    assert buy_row.valor_operacao == Decimal("10.37")


def test_reimport_replaces_rows() -> None:
    conn = _conn()
    save_movimentacao_report(conn, _make_report(2024))
    # Re-import with empty rows
    empty = MovimentacaoReport(year=2024, rows=[])
    save_movimentacao_report(conn, empty)
    loaded = load_movimentacao_report(conn, 2024)
    assert loaded is not None
    assert not loaded.rows
    # Only one import_log entry
    count = conn.execute(
        "SELECT COUNT(*) FROM import_log WHERE year=2024 AND source_type='movimentacao'"
    ).fetchone()[0]
    assert count == 1
