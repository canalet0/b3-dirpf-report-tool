from decimal import Decimal
from typing import cast

from contabilidade.parser.sheet_parser import (
    _parse_acoes,
    _parse_emprestimos,
    _parse_etfs,
    _parse_fundos,
    _parse_proventos,
    _parse_reembolsos,
    _parse_renda_fixa,
    _parse_tesouro_direto,
    _to_decimal,
)

Rows = list[list[str | None]]


def _r(rows: list[list[str]]) -> Rows:
    return cast(Rows, rows)


# ---------------------------------------------------------------------------
# _to_decimal
# ---------------------------------------------------------------------------


def test_to_decimal_none_returns_zero() -> None:
    assert _to_decimal(None) == Decimal("0")


def test_to_decimal_dash_returns_zero() -> None:
    assert _to_decimal("-") == Decimal("0")


def test_to_decimal_empty_returns_zero() -> None:
    assert _to_decimal("") == Decimal("0")


def test_to_decimal_dot_decimal_float_string() -> None:
    assert _to_decimal("143.85") == Decimal("143.85")


def test_to_decimal_integer_string() -> None:
    assert _to_decimal("7") == Decimal("7")


def test_to_decimal_br_format_with_thousands() -> None:
    assert _to_decimal("1.270,19") == Decimal("1270.19")


def test_to_decimal_comma_only() -> None:
    assert _to_decimal("1270,19") == Decimal("1270.19")


# ---------------------------------------------------------------------------
# _parse_acoes
# ---------------------------------------------------------------------------

_ACAO_HEADER = [
    "Produto",
    "Instituição",
    "Conta",
    "Código de Negociação",
    "CNPJ da Empresa",
    "Código ISIN / Distribuição",
    "Tipo",
    "Escriturador",
    "Quantidade",
    "Quantidade Disponível",
    "Quantidade Indisponível",
    "Motivo",
    "Preço de Fechamento",
    "Valor Atualizado",
]


def test_parse_acoes_basic() -> None:
    rows = [
        _ACAO_HEADER,
        [
            "ITSA4 - ITAUSA S.A.",
            "INTER",
            "1234",
            "ITSA4",
            "61532644000115",
            "BRITSAACNPR7",
            "PN",
            "ITAU CV",
            "143.85",
            "143.85",
            "-",
            "-",
            "8.83",
            "1270.19",
        ],
    ]
    result = _parse_acoes(_r(rows))
    assert len(result) == 1
    acao = result[0]
    assert acao.codigo_negociacao == "ITSA4"
    assert acao.quantidade == Decimal("143.85")
    assert acao.valor_atualizado == Decimal("1270.19")
    assert acao.cnpj_empresa == "61532644000115"


def test_parse_acoes_skips_empty_first_column() -> None:
    rows = [
        _ACAO_HEADER,
        [
            "",
            "INTER",
            "1234",
            "X",
            "CNPJ",
            "ISIN",
            "ON",
            "ESC",
            "1",
            "1",
            "-",
            "-",
            "10",
            "10",
        ],
    ]
    assert not _parse_acoes(_r(rows))


def test_parse_acoes_empty_sheet() -> None:
    assert not _parse_acoes([])


# ---------------------------------------------------------------------------
# _parse_emprestimos
# ---------------------------------------------------------------------------

_EMP_HEADER = [
    "Produto",
    "Instituição",
    "Natureza",
    "Número de Contrato",
    "Modalidade",
    "OPA",
    "Liquidação antecipada",
    "Taxa",
    "Comissão",
    "Data de registro",
    "Data de vencimento",
    "Quantidade",
    "Preço de Fechamento",
    "Valor Atualizado",
]


def test_parse_emprestimos_basic() -> None:
    rows = [
        _EMP_HEADER,
        [
            "TAEE11 - TAESA",
            "INTER",
            "Doador",
            "CONT001",
            "BTC",
            "N",
            "N",
            "0.32",
            "0",
            "01/01/2024",
            "04/02/2025",
            "34",
            "13.5",
            "459.0",
        ],
    ]
    result = _parse_emprestimos(_r(rows))
    assert len(result) == 1
    assert result[0].natureza == "Doador"
    assert result[0].quantidade == Decimal("34")
    assert result[0].taxa == Decimal("0.32")


# ---------------------------------------------------------------------------
# _parse_etfs
# ---------------------------------------------------------------------------

_ETF_HEADER = [
    "Produto",
    "Instituição",
    "Conta",
    "Código de Negociação",
    "CNPJ do Fundo",
    "Código ISIN / Distribuição",
    "Tipo",
    "Quantidade",
    "Quantidade Disponível",
    "Quantidade Indisponível",
    "Motivo",
    "Preço de Fechamento",
    "Valor Atualizado",
]


def test_parse_etfs_basic() -> None:
    rows = [
        _ETF_HEADER,
        [
            "HASH11 - HASHDEX CRIPTO FDO",
            "INTER",
            "1234",
            "HASH11",
            "35340541000144",
            "BRHASHCTF006",
            "Criptoativo",
            "10",
            "10",
            "-",
            "-",
            "50.0",
            "500.0",
        ],
    ]
    result = _parse_etfs(_r(rows))
    assert len(result) == 1
    assert result[0].tipo == "Criptoativo"
    assert result[0].valor_atualizado == Decimal("500.0")


# ---------------------------------------------------------------------------
# _parse_fundos
# ---------------------------------------------------------------------------

_FUNDO_HEADER = [
    "Produto",
    "Instituição",
    "Conta",
    "Código de Negociação",
    "CNPJ do Fundo",
    "Código ISIN / Distribuição",
    "Tipo",
    "Administrador",
    "Quantidade",
    "Quantidade Disponível",
    "Quantidade Indisponível",
    "Motivo",
    "Preço de Fechamento",
    "Valor Atualizado",
]


def test_parse_fundos_basic() -> None:
    rows = [
        _FUNDO_HEADER,
        [
            "HGRE11 - CSHG REAL ESTATE FII",
            "INTER",
            "1234",
            "HGRE11",
            "09072017000129",
            "BRHGRECTF010",
            "Cotas",
            "CREDIT SUISSE",
            "5",
            "5",
            "-",
            "-",
            "120.0",
            "600.0",
        ],
    ]
    result = _parse_fundos(_r(rows))
    assert len(result) == 1
    assert result[0].administrador == "CREDIT SUISSE"
    assert result[0].valor_atualizado == Decimal("600.0")


# ---------------------------------------------------------------------------
# _parse_renda_fixa
# ---------------------------------------------------------------------------

_RF_HEADER = [
    "Produto",
    "Instituição",
    "Emissor",
    "Código",
    "Indexador",
    "Tipo de regime",
    "Data de Emissão",
    "Vencimento",
    "Quantidade",
    "Quantidade Disponível",
    "Quantidade Indisponível",
    "Motivo",
    "Contraparte",
    "Preço Atualizado MTM",
    "Valor Atualizado MTM",
    "Preço Atualizado CURVA",
    "Valor Atualizado CURVA",
]


def test_parse_renda_fixa_uses_curva_value() -> None:
    rows = [
        _RF_HEADER,
        [
            "CDB - BANCO X",
            "INTER",
            "BANCO X",
            "CDB001",
            "DI",
            "Depositado",
            "01/01/2023",
            "01/01/2025",
            "1",
            "1",
            "-",
            "-",
            "INTER",
            "100.5",
            "100.5",
            "101.0",
            "101.0",
        ],
    ]
    result = _parse_renda_fixa(_r(rows))
    assert len(result) == 1
    assert result[0].valor_atualizado_curva == Decimal("101.0")


def test_parse_renda_fixa_dash_mtm_uses_curva() -> None:
    rows = [
        _RF_HEADER,
        [
            "LCA - BANCO Y",
            "INTER",
            "BANCO Y",
            "LCA001",
            "DI",
            "Depositado",
            "01/06/2023",
            "01/06/2025",
            "1",
            "1",
            "-",
            "-",
            "INTER",
            "-",
            "-",
            "200.0",
            "200.0",
        ],
    ]
    result = _parse_renda_fixa(_r(rows))
    assert result[0].valor_atualizado_curva == Decimal("200.0")


# ---------------------------------------------------------------------------
# _parse_tesouro_direto
# ---------------------------------------------------------------------------

_TESOURO_HEADER = [
    "Produto",
    "Instituição",
    "Código ISIN",
    "Indexador",
    "Vencimento",
    "Quantidade",
    "Quantidade Disponível",
    "Quantidade Indisponível",
    "Motivo",
    "Valor Aplicado",
    "Valor bruto",
    "Valor líquido",
    "Valor Atualizado",
]


def test_parse_tesouro_direto_basic() -> None:
    rows = [
        _TESOURO_HEADER,
        [
            "Tesouro IPCA+ 2026",
            "INTER",
            "BRSTNJNTF1R8",
            "IPCA+",
            "15/08/2026",
            "0.41",
            "0.41",
            "-",
            "-",
            "500.0",
            "530.0",
            "520.0",
            "525.0",
        ],
    ]
    result = _parse_tesouro_direto(_r(rows))
    assert len(result) == 1
    assert result[0].produto == "Tesouro IPCA+ 2026"
    assert result[0].valor_aplicado == Decimal("500.0")
    assert result[0].valor_atualizado == Decimal("525.0")


# ---------------------------------------------------------------------------
# _parse_proventos
# ---------------------------------------------------------------------------


def test_parse_proventos_dividendo() -> None:
    rows = [
        ["Produto", "Tipo de Evento", "Valor líquido"],
        ["ITSA4", "Dividendo", "41.16"],
    ]
    result = _parse_proventos(_r(rows))
    assert result[0].tipo_evento == "Dividendo"
    assert result[0].valor_liquido == Decimal("41.16")


def test_parse_proventos_jcp() -> None:
    rows = [
        ["Produto", "Tipo de Evento", "Valor líquido"],
        ["VALE3", "Juros Sobre Capital Próprio", "19.50"],
    ]
    result = _parse_proventos(_r(rows))
    assert result[0].tipo_evento == "Juros Sobre Capital Próprio"


def test_parse_proventos_empty_sheet() -> None:
    assert not _parse_proventos([])


# ---------------------------------------------------------------------------
# _parse_reembolsos
# ---------------------------------------------------------------------------


def test_parse_reembolsos_basic() -> None:
    rows = [
        ["Produto", "Tipo de Evento", "Valor líquido"],
        ["TAEE11", "Reembolso", "65.23"],
    ]
    result = _parse_reembolsos(_r(rows))
    assert result[0].produto == "TAEE11"
    assert result[0].valor_liquido == Decimal("65.23")
