import sqlite3
from decimal import Decimal

from contabilidade.db.b3_repository import load_b3_report, save_b3_report
from contabilidade.db.schema import ensure_schema
from contabilidade.models.b3 import (
    AcaoPosition,
    B3Report,
    EmprestimoPosition,
    EtfPosition,
    FundoPosition,
    Provento,
    Reembolso,
    RendaFixaPosition,
    TesouroDiretoPosition,
)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def _make_report(year: int = 2024) -> B3Report:
    return B3Report(
        year=year,
        acoes=[
            AcaoPosition(
                produto="ITSA4 - ITAUSA S.A.",
                instituicao="INTER",
                conta="1234",
                codigo_negociacao="ITSA4",
                cnpj_empresa="61532644000115",
                codigo_isin="BRITSAACNPR7",
                tipo="PN",
                escriturador="ITAU CV",
                quantidade=Decimal("143.85"),
                quantidade_disponivel=Decimal("143.85"),
                preco_fechamento=Decimal("8.83"),
                valor_atualizado=Decimal("1270.19"),
            )
        ],
        emprestimos=[
            EmprestimoPosition(
                produto="TAEE11 - TAESA",
                instituicao="INTER",
                natureza="Doador",
                numero_contrato="C001",
                taxa=Decimal("0.32"),
                data_registro="01/01/2024",
                data_vencimento="04/02/2025",
                quantidade=Decimal("34"),
                valor_atualizado=Decimal("1000.00"),
            )
        ],
        etfs=[
            EtfPosition(
                produto="HASH11 - HASHDEX",
                instituicao="INTER",
                conta="1234",
                codigo_negociacao="HASH11",
                cnpj_fundo="35340541000144",
                codigo_isin="BRHASHCTF006",
                tipo="Criptoativo",
                quantidade=Decimal("19"),
                preco_fechamento=Decimal("33.42"),
                valor_atualizado=Decimal("634.98"),
            )
        ],
        fundos=[
            FundoPosition(
                produto="HGRE11 - CSHG REAL ESTATE",
                instituicao="INTER",
                conta="1234",
                codigo_negociacao="HGRE11",
                cnpj_fundo="09072017000129",
                codigo_isin="BRHGRECTF010",
                tipo="Cotas",
                administrador="CREDIT SUISSE",
                quantidade=Decimal("5"),
                preco_fechamento=Decimal("120.00"),
                valor_atualizado=Decimal("600.00"),
            )
        ],
        renda_fixa=[
            RendaFixaPosition(
                produto="CDB - BANCO X",
                instituicao="INTER",
                emissor="BANCO X",
                codigo="CDB001",
                indexador="DI",
                tipo_regime="Depositado",
                data_emissao="01/01/2023",
                vencimento="01/01/2025",
                quantidade=Decimal("1"),
                valor_atualizado_curva=Decimal("1000.00"),
            )
        ],
        tesouro_direto=[
            TesouroDiretoPosition(
                produto="Tesouro IPCA+ 2026",
                instituicao="INTER",
                codigo_isin="BRSTNJNTF1R8",
                indexador="IPCA+",
                vencimento="15/08/2026",
                quantidade=Decimal("0.41"),
                valor_aplicado=Decimal("500.00"),
                valor_atualizado=Decimal("525.00"),
            )
        ],
        proventos=[
            Provento(
                produto="ITSA4", tipo_evento="Dividendo", valor_liquido=Decimal("41.16")
            )
        ],
        reembolsos=[
            Reembolso(
                produto="TAEE11",
                tipo_evento="Reembolso",
                valor_liquido=Decimal("30.00"),
            )
        ],
    )


def test_save_and_load_b3_report_roundtrip() -> None:
    conn = _conn()
    original = _make_report(2024)
    save_b3_report(conn, original)
    loaded = load_b3_report(conn, 2024)
    assert loaded is not None
    assert loaded.year == original.year
    assert loaded.acoes == original.acoes
    assert loaded.emprestimos == original.emprestimos
    assert loaded.etfs == original.etfs
    assert loaded.fundos == original.fundos
    assert loaded.renda_fixa == original.renda_fixa
    assert loaded.tesouro_direto == original.tesouro_direto
    assert loaded.proventos == original.proventos
    assert loaded.reembolsos == original.reembolsos


def test_save_b3_report_replaces_on_reimport() -> None:
    conn = _conn()
    save_b3_report(conn, _make_report(2024))
    # Re-import with different data (empty lists)
    empty = B3Report(
        year=2024,
        acoes=[],
        emprestimos=[],
        etfs=[],
        fundos=[],
        renda_fixa=[],
        tesouro_direto=[],
        proventos=[],
        reembolsos=[],
    )
    save_b3_report(conn, empty)
    loaded = load_b3_report(conn, 2024)
    assert loaded is not None
    assert not loaded.acoes
    # Only one import_log entry for b3_report
    count = conn.execute(
        "SELECT COUNT(*) FROM import_log WHERE year=2024 AND source_type='b3_report'"
    ).fetchone()[0]
    assert count == 1


def test_load_b3_report_returns_none_when_missing() -> None:
    conn = _conn()
    assert load_b3_report(conn, 2024) is None


def test_decimal_precision_preserved() -> None:
    conn = _conn()
    report = _make_report(2024)
    save_b3_report(conn, report)
    loaded = load_b3_report(conn, 2024)
    assert loaded is not None
    assert loaded.acoes[0].valor_atualizado == Decimal("1270.19")
    assert loaded.acoes[0].quantidade == Decimal("143.85")


def test_empty_lists_roundtrip() -> None:
    conn = _conn()
    empty = B3Report(
        year=2023,
        acoes=[],
        emprestimos=[],
        etfs=[],
        fundos=[],
        renda_fixa=[],
        tesouro_direto=[],
        proventos=[],
        reembolsos=[],
    )
    save_b3_report(conn, empty)
    loaded = load_b3_report(conn, 2023)
    assert loaded is not None
    assert not loaded.acoes
    assert not loaded.proventos
