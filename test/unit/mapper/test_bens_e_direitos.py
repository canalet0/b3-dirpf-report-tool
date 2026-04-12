from decimal import Decimal

from contabilidade.mapper.bens_e_direitos import (
    _format_cnpj,
    _is_fii,
    _renda_fixa_codigo,
    _ticker_from_produto,
    map_acoes,
    map_etfs,
    map_fundos,
    map_renda_fixa,
    map_tesouro_direto,
)
from contabilidade.models.b3 import (
    AcaoPosition,
    EtfPosition,
    FundoPosition,
    RendaFixaPosition,
    TesouroDiretoPosition,
)


def _make_acao() -> AcaoPosition:
    return AcaoPosition(
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


def test_format_cnpj_14_digits() -> None:
    assert _format_cnpj("61532644000115") == "61.532.644/0001-15"


def test_format_cnpj_already_formatted() -> None:
    assert _format_cnpj("61.532.644/0001-15") == "61.532.644/0001-15"


def test_format_cnpj_invalid_length() -> None:
    assert _format_cnpj("123") == "123"


def test_ticker_from_produto_standard() -> None:
    ticker, company = _ticker_from_produto("ITSA4 - ITAUSA S.A.")
    assert ticker == "ITSA4"
    assert company == "ITAUSA S.A."


def test_ticker_from_produto_no_separator() -> None:
    ticker, company = _ticker_from_produto("JUSTSOMETHING")
    assert ticker == "JUSTSOMETHING"
    assert company == "JUSTSOMETHING"


def test_is_fii_detects_imob() -> None:
    assert _is_fii("HGRE11 - CSHG REAL ESTATE FII IMOB") is True


def test_is_fii_detects_fii() -> None:
    assert _is_fii("RBRF11 - RBR ALPHA FII") is True


def test_is_fii_false_for_regular_fund() -> None:
    assert _is_fii("SOME FUND REGULAR") is False


def test_renda_fixa_codigo_cdb_is_02() -> None:
    assert _renda_fixa_codigo("CDB - BANCO X") == "02"


def test_renda_fixa_codigo_lca_is_02() -> None:
    assert _renda_fixa_codigo("LCA - BANCO Y") == "02"


def test_renda_fixa_codigo_debenture_is_03() -> None:
    assert _renda_fixa_codigo("DEB - EMPRESA X") == "03"


def test_map_acoes_returns_correct_grupo_codigo() -> None:
    result = map_acoes([_make_acao()], 2024)
    assert len(result) == 1
    assert result[0].grupo == "03"
    assert result[0].codigo == "01"


def test_map_acoes_formats_cnpj() -> None:
    result = map_acoes([_make_acao()], 2024)
    assert result[0].cnpj == "61.532.644/0001-15"


def test_map_acoes_valor_atual_correct() -> None:
    result = map_acoes([_make_acao()], 2024)
    assert result[0].valor_atual == Decimal("1270.19")


def test_map_acoes_valor_anterior_zero() -> None:
    result = map_acoes([_make_acao()], 2024)
    assert result[0].valor_anterior == Decimal("0")


def test_map_acoes_discriminacao_contains_ticker() -> None:
    result = map_acoes([_make_acao()], 2024)
    assert "ITSA4" in result[0].discriminacao


def test_map_acoes_discriminacao_contains_previous_year_note() -> None:
    result = map_acoes([_make_acao()], 2024)
    assert "PREENCHER" in result[0].discriminacao


def test_map_etfs_grupo_07_codigo_09() -> None:
    etf = EtfPosition(
        produto="HASH11 - HASHDEX CRIPTO",
        instituicao="INTER",
        conta="1234",
        codigo_negociacao="HASH11",
        cnpj_fundo="35340541000144",
        codigo_isin="BRHASHCTF006",
        tipo="Criptoativo",
        quantidade=Decimal("10"),
        preco_fechamento=Decimal("50.0"),
        valor_atualizado=Decimal("500.0"),
    )
    result = map_etfs([etf], 2024)
    assert result[0].grupo == "07"
    assert result[0].codigo == "09"


def test_map_fundos_grupo_07_codigo_03() -> None:
    fundo = FundoPosition(
        produto="HGRE11 - CSHG REAL ESTATE FII",
        instituicao="INTER",
        conta="1234",
        codigo_negociacao="HGRE11",
        cnpj_fundo="09072017000129",
        codigo_isin="BRHGRECTF010",
        tipo="Cotas",
        administrador="CREDIT SUISSE",
        quantidade=Decimal("5"),
        preco_fechamento=Decimal("120.0"),
        valor_atualizado=Decimal("600.0"),
    )
    result = map_fundos([fundo], 2024)
    assert result[0].grupo == "07"
    assert result[0].codigo == "03"
    assert "Fundo de Investimento Imobiliário (FII)" in result[0].discriminacao


def test_map_renda_fixa_cdb_codigo_02() -> None:
    rf = RendaFixaPosition(
        produto="CDB - BANCO X",
        instituicao="INTER",
        emissor="BANCO X",
        codigo="CDB001",
        indexador="DI",
        tipo_regime="Depositado",
        data_emissao="01/01/2023",
        vencimento="01/01/2025",
        quantidade=Decimal("1"),
        valor_atualizado_curva=Decimal("1000.0"),
    )
    result = map_renda_fixa([rf], 2024)
    assert result[0].grupo == "04"
    assert result[0].codigo == "02"
    assert result[0].valor_atual == Decimal("1000.0")


def test_map_tesouro_direto_codigo_04() -> None:
    td = TesouroDiretoPosition(
        produto="Tesouro IPCA+ 2026",
        instituicao="INTER",
        codigo_isin="BRSTNJNTF1R8",
        indexador="IPCA+",
        vencimento="15/08/2026",
        quantidade=Decimal("0.41"),
        valor_aplicado=Decimal("500.0"),
        valor_atualizado=Decimal("525.0"),
    )
    result = map_tesouro_direto([td], 2024)
    assert result[0].grupo == "04"
    assert result[0].codigo == "04"
    assert result[0].valor_atual == Decimal("525.0")
