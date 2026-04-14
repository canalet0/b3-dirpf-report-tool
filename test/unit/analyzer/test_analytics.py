from decimal import Decimal

import pytest

from contabilidade.analyzer.analytics import (
    _CostBasis,
    _build_allocation,
    _build_cost_basis,
    _build_dividend_yields,
    _build_overall_performance,
    _build_performance,
    _pct,
)
from contabilidade.models.analytics import AssetPerformance
from contabilidade.models.b3 import (
    AcaoPosition,
    B3Report,
    FundoPosition,
    Provento,
    RendaFixaPosition,
    TesouroDiretoPosition,
)
from contabilidade.models.movimentacao import MovimentacaoRow


def _acao(ticker: str, valor: str) -> AcaoPosition:
    return AcaoPosition(
        produto=ticker,
        instituicao="XP",
        conta="123",
        codigo_negociacao=ticker,
        cnpj_empresa="00.000.000/0001-00",
        codigo_isin="BR000000001",
        tipo="PN",
        escriturador="",
        quantidade=Decimal("10"),
        quantidade_disponivel=Decimal("10"),
        preco_fechamento=Decimal("10"),
        valor_atualizado=Decimal(valor),
    )


def _fundo(produto: str, valor: str) -> FundoPosition:
    return FundoPosition(
        produto=produto,
        instituicao="XP",
        conta="123",
        codigo_negociacao=produto.split(" - ")[0],
        cnpj_fundo="00.000.000/0001-00",
        codigo_isin="BR000000002",
        tipo="FII",
        administrador="ADM",
        quantidade=Decimal("10"),
        preco_fechamento=Decimal("10"),
        valor_atualizado=Decimal(valor),
    )


def _renda_fixa(codigo: str, valor: str) -> RendaFixaPosition:
    return RendaFixaPosition(
        produto=f"CDB {codigo}",
        instituicao="XP",
        emissor="BANCO",
        codigo=codigo,
        indexador="CDI",
        tipo_regime="CURVA",
        data_emissao="01/01/2023",
        vencimento="01/01/2026",
        quantidade=Decimal("1"),
        valor_atualizado_curva=Decimal(valor),
    )


def _tesouro(produto: str, aplicado: str, atualizado: str) -> TesouroDiretoPosition:
    return TesouroDiretoPosition(
        produto=produto,
        instituicao="XP",
        codigo_isin="BRSTNNTNB165",
        indexador="IPCA",
        vencimento="15/05/2035",
        quantidade=Decimal("1"),
        valor_aplicado=Decimal(aplicado),
        valor_atualizado=Decimal(atualizado),
    )


def _b3(
    acoes: list[AcaoPosition] | None = None,
    fundos: list[FundoPosition] | None = None,
    renda_fixa: list[RendaFixaPosition] | None = None,
    tesouro: list[TesouroDiretoPosition] | None = None,
    proventos: list[Provento] | None = None,
) -> B3Report:
    return B3Report(
        year=2024,
        acoes=acoes or [],
        emprestimos=[],
        etfs=[],
        fundos=fundos or [],
        renda_fixa=renda_fixa or [],
        tesouro_direto=tesouro or [],
        proventos=proventos or [],
        reembolsos=[],
    )


def _row(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    ticker: str,
    entrada_saida: str,
    movimentacao: str,
    qty: str | None,
    price: str | None,
    data: str = "01/01/2024",
) -> MovimentacaoRow:
    return MovimentacaoRow(
        entrada_saida=entrada_saida,
        data=data,
        movimentacao=movimentacao,
        produto=f"{ticker} - Company",
        instituicao="XP",
        quantidade=Decimal(qty) if qty else None,
        preco_unitario=Decimal(price) if price else None,
        valor_operacao=Decimal(qty) * Decimal(price) if qty and price else None,
    )


# --- cost basis ---


def test_build_cost_basis_empty_returns_empty() -> None:
    assert not _build_cost_basis([])


def test_build_cost_basis_single_buy() -> None:
    rows = [_row("ITSA4", "Credito", "Compra", "10", "20.00")]
    cb = _build_cost_basis(rows)
    assert "ITSA4" in cb
    assert cb["ITSA4"].avg == Decimal("20.00")
    assert cb["ITSA4"].qty == Decimal("10")


def test_build_cost_basis_weighted_average_two_buys() -> None:
    rows = [
        _row("ITSA4", "Credito", "Compra", "10", "20.00", "01/01/2024"),
        _row("ITSA4", "Credito", "Compra", "10", "30.00", "02/01/2024"),
    ]
    cb = _build_cost_basis(rows)
    assert cb["ITSA4"].avg == Decimal("25.00")
    assert cb["ITSA4"].qty == Decimal("20")


def test_build_cost_basis_sell_decrements_qty() -> None:
    rows = [
        _row("ITSA4", "Credito", "Compra", "10", "20.00", "01/01/2024"),
        _row(
            "ITSA4", "Debito", "Transferência - Liquidação", "4", "25.00", "02/01/2024"
        ),
    ]
    cb = _build_cost_basis(rows)
    assert cb["ITSA4"].qty == Decimal("6")
    assert cb["ITSA4"].avg == Decimal("20.00")


def test_build_cost_basis_full_sell_removes_ticker() -> None:
    rows = [
        _row("ITSA4", "Credito", "Compra", "10", "20.00", "01/01/2024"),
        _row(
            "ITSA4", "Debito", "Transferência - Liquidação", "10", "25.00", "02/01/2024"
        ),
    ]
    cb = _build_cost_basis(rows)
    assert "ITSA4" not in cb


# --- allocation ---


def test_build_allocation_splits_fii_from_fundos() -> None:
    fundos = [
        _fundo("HGLG11 - FII CSHG LOG", "5000"),
        _fundo("FUND1 - Fundo Convencional", "3000"),
    ]
    alloc = _build_allocation(_b3(fundos=fundos))
    assert alloc.fiis == Decimal("5000")
    assert alloc.fundos == Decimal("3000")
    assert alloc.total == Decimal("8000")


def test_build_allocation_pct_zero_total_returns_zero() -> None:
    alloc = _build_allocation(_b3())
    assert alloc.pct_acoes == Decimal("0")
    assert alloc.total == Decimal("0")


# --- performance ---


def test_build_performance_tesouro_uses_valor_aplicado() -> None:
    tesouro = [_tesouro("Tesouro IPCA+ 2035", "1000", "1200")]
    perf = _build_performance(_b3(tesouro=tesouro), {})
    assert len(perf) == 1
    p = perf[0]
    assert p.cost_basis == Decimal("1000")
    assert p.total_return == Decimal("200")
    assert p.total_return_pct == Decimal("20.00")


def test_build_performance_renda_fixa_has_no_cost_basis() -> None:
    rf = [_renda_fixa("CDB001", "5000")]
    perf = _build_performance(_b3(renda_fixa=rf), {})
    assert len(perf) == 1
    p = perf[0]
    assert p.cost_basis is None
    assert p.total_return is None
    assert p.total_return_pct is None


def test_build_performance_acao_with_cost_basis() -> None:
    acoes = [_acao("ITSA4", "2500")]
    cb = {"ITSA4": _CostBasis(avg=Decimal("20.00"), qty=Decimal("100"))}
    perf = _build_performance(_b3(acoes=acoes), cb)
    p = next(x for x in perf if x.ticker == "ITSA4")
    assert p.cost_basis == Decimal("2000.00")
    assert p.total_return == Decimal("500")


# --- dividend yields ---


def test_build_dividend_yields_no_position_match_gives_none_yield() -> None:
    # ticker in proventos but no matching position
    proventos = [
        Provento(
            produto="SOLD4 - Company",
            tipo_evento="Dividendo",
            valor_liquido=Decimal("100"),
        )
    ]
    yields = _build_dividend_yields(_b3(proventos=proventos))
    assert len(yields) == 1
    assert yields[0].current_value == Decimal("0")
    assert yields[0].yield_pct is None


def test_build_dividend_yields_with_position_match() -> None:
    acoes = [_acao("ITSA4", "1000")]
    proventos = [
        Provento(
            produto="ITSA4 - Itausa",
            tipo_evento="Dividendo",
            valor_liquido=Decimal("50"),
        )
    ]
    yields = _build_dividend_yields(_b3(acoes=acoes, proventos=proventos))
    assert len(yields) == 1
    y = yields[0]
    assert y.current_value == Decimal("1000")
    assert y.yield_pct == Decimal("5.00")


# --- _pct helper ---


def test_pct_zero_denominator_returns_zero() -> None:
    assert _pct(Decimal("100"), Decimal("0")) == Decimal("0")


def test_pct_normal_calculation() -> None:
    assert _pct(Decimal("25"), Decimal("100")) == Decimal("25.00")


@pytest.mark.parametrize("qty,price", [("0", "20"), ("10", None)])
def test_build_cost_basis_ignores_invalid_buy(qty: str, price: str | None) -> None:
    rows = [_row("ITSA4", "Credito", "Compra", qty if qty != "0" else "0", price)]
    cb = _build_cost_basis(rows)
    assert "ITSA4" not in cb


# --- overall performance ---


def _perf(
    ticker: str,
    asset_class: str,
    current: str,
    cost: str | None,
) -> AssetPerformance:
    cb = Decimal(cost) if cost else None
    ret = (Decimal(current) - cb) if cb is not None else None
    ret_pct = (
        (ret / cb * Decimal("100")).quantize(Decimal("0.01"))
        if ret is not None and cb is not None and cb != Decimal("0")
        else None
    )
    return AssetPerformance(
        ticker=ticker,
        nome=ticker,
        asset_class=asset_class,
        current_value=Decimal(current),
        cost_basis=cb,
        total_return=ret,
        total_return_pct=ret_pct,
    )


def test_build_overall_performance_empty() -> None:
    op = _build_overall_performance([])
    assert op.total_current == Decimal("0")
    assert op.total_cost is None
    assert op.total_return is None
    assert not op.by_class


def test_build_overall_performance_sums_totals() -> None:
    perfs = [
        _perf("ITSA4", "acao", "1000", "800"),
        _perf("BOVA11", "etf", "2000", "1500"),
    ]
    op = _build_overall_performance(perfs)
    assert op.total_current == Decimal("3000")
    assert op.total_cost == Decimal("2300")
    assert op.total_return == Decimal("700")
    assert op.total_return_pct == Decimal("30.43")


def test_build_overall_performance_no_cost_basis() -> None:
    perfs = [_perf("CDB001", "renda_fixa", "5000", None)]
    op = _build_overall_performance(perfs)
    assert op.total_current == Decimal("5000")
    assert op.total_cost is None
    assert op.total_return is None


def test_build_overall_performance_class_order() -> None:
    perfs = [
        _perf("TD", "tesouro", "1000", "900"),
        _perf("ITSA4", "acao", "500", "400"),
    ]
    op = _build_overall_performance(perfs)
    classes = [cp.asset_class for cp in op.by_class]
    assert classes.index("acao") < classes.index("tesouro")


def test_build_overall_performance_mixed_cost_basis() -> None:
    # Some classes with cost, some without
    perfs = [
        _perf("ITSA4", "acao", "1000", "800"),
        _perf("CDB001", "renda_fixa", "5000", None),
    ]
    op = _build_overall_performance(perfs)
    assert op.total_current == Decimal("6000")
    assert op.total_cost == Decimal("800")  # only acao contributes
    acao_cp = next(cp for cp in op.by_class if cp.asset_class == "acao")
    rf_cp = next(cp for cp in op.by_class if cp.asset_class == "renda_fixa")
    assert acao_cp.cost_basis == Decimal("800")
    assert rf_cp.cost_basis is None
