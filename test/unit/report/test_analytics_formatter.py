from decimal import Decimal

from contabilidade.models.analytics import (
    AllocationBreakdown,
    AnalyticsReport,
    AssetPerformance,
    ClassPerformance,
    CostBasisEntry,
    DividendYield,
    OverallPerformance,
)
from contabilidade.report.analytics_formatter import _brl, format_analytics_report

_DB_LABEL = "~/.contabilidade/data.db"


def _make_allocation() -> AllocationBreakdown:
    return AllocationBreakdown(
        year=2024,
        acoes=Decimal("1000"),
        fiis=Decimal("500"),
        fundos=Decimal("0"),
        etfs=Decimal("0"),
        renda_fixa=Decimal("0"),
        tesouro=Decimal("0"),
        total=Decimal("1500"),
        pct_acoes=Decimal("66.67"),
        pct_fiis=Decimal("33.33"),
        pct_fundos=Decimal("0"),
        pct_etfs=Decimal("0"),
        pct_renda_fixa=Decimal("0"),
        pct_tesouro=Decimal("0"),
    )


def _make_overall(has_movimentacao: bool = True) -> OverallPerformance:
    cp = ClassPerformance(
        asset_class="acao",
        current_value=Decimal("1000"),
        cost_basis=Decimal("800") if has_movimentacao else None,
        total_return=Decimal("200") if has_movimentacao else None,
        total_return_pct=Decimal("25.00") if has_movimentacao else None,
    )
    return OverallPerformance(
        total_current=Decimal("1000"),
        total_cost=Decimal("800") if has_movimentacao else None,
        total_return=Decimal("200") if has_movimentacao else None,
        total_return_pct=Decimal("25.00") if has_movimentacao else None,
        by_class=[cp],
    )


def _make_report(has_movimentacao: bool = True) -> AnalyticsReport:
    perf = AssetPerformance(
        ticker="ITSA4",
        nome="ITSA4 - Itausa",
        asset_class="acao",
        current_value=Decimal("1000"),
        cost_basis=Decimal("800") if has_movimentacao else None,
        total_return=Decimal("200") if has_movimentacao else None,
        total_return_pct=Decimal("25.00") if has_movimentacao else None,
    )
    dy = DividendYield(
        ticker="ITSA4",
        nome="Itausa",
        proventos_ano=Decimal("50"),
        current_value=Decimal("1000"),
        yield_pct=Decimal("5.00"),
    )
    cb = CostBasisEntry(
        ticker="ITSA4",
        nome="ITSA4",
        avg_price=Decimal("8.00"),
        quantity=Decimal("100"),
        total_cost=Decimal("800"),
    )
    return AnalyticsReport(
        year=2024,
        has_movimentacao=has_movimentacao,
        overall_performance=_make_overall(has_movimentacao),
        performance=[perf],
        dividend_yields=[dy],
        cost_basis=[cb] if has_movimentacao else [],
        allocation=_make_allocation(),
    )


def test_brl_formats_correctly() -> None:
    assert _brl(Decimal("1270.19")) == "R$ 1.270,19"
    assert _brl(Decimal("0")) == "R$ 0,00"


def test_format_no_movimentacao_shows_note() -> None:
    report = _make_report(has_movimentacao=False)
    content = format_analytics_report(report, _DB_LABEL)
    assert "Nenhum dado de movimentação importado" in content


def test_format_overall_section_present() -> None:
    report = _make_report()
    content = format_analytics_report(report, _DB_LABEL)
    assert "PERFORMANCE GERAL DA CARTEIRA" in content
    assert "Patrimônio Atual" in content


def test_format_overall_shows_return_with_movimentacao() -> None:
    report = _make_report(has_movimentacao=True)
    content = format_analytics_report(report, _DB_LABEL)
    assert "Custo Total Investido" in content
    assert "Retorno" in content
    assert "+25,00%" in content


def test_format_ticker_appears_in_performance_section() -> None:
    report = _make_report()
    content = format_analytics_report(report, _DB_LABEL)
    assert "ITSA4" in content
    assert "DESEMPENHO POR ATIVO" in content


def test_yield_none_renders_as_dash() -> None:
    alloc = _make_allocation()
    dy_none = DividendYield(
        ticker="SOLD4",
        nome="Sold",
        proventos_ano=Decimal("10"),
        current_value=Decimal("0"),
        yield_pct=None,
    )
    overall = OverallPerformance(
        total_current=Decimal("0"),
        total_cost=None,
        total_return=None,
        total_return_pct=None,
        by_class=[],
    )
    report = AnalyticsReport(
        year=2024,
        has_movimentacao=False,
        overall_performance=overall,
        performance=[],
        dividend_yields=[dy_none],
        cost_basis=[],
        allocation=alloc,
    )
    content = format_analytics_report(report, _DB_LABEL)
    assert "—" in content


def test_format_cost_basis_section_hidden_without_movimentacao() -> None:
    report = _make_report(has_movimentacao=False)
    content = format_analytics_report(report, _DB_LABEL)
    assert "CUSTO MÉDIO POR ATIVO" in content
    assert "import YEAR --movimentacao" in content


def test_format_cost_basis_section_shows_entries_with_movimentacao() -> None:
    report = _make_report(has_movimentacao=True)
    content = format_analytics_report(report, _DB_LABEL)
    assert "ITSA4" in content
    assert "R$ 8,00" in content
