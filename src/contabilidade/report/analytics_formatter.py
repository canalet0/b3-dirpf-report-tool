from datetime import datetime
from decimal import Decimal

from contabilidade.models.analytics import (
    AllocationBreakdown,
    AnalyticsReport,
    AssetPerformance,
    CostBasisEntry,
    DividendYield,
    OverallPerformance,
)

_ASSET_CLASS_LABELS = {
    "acao": "Ação",
    "etf": "ETF",
    "fundo_fii": "FII",
    "fundo": "Fundo",
    "renda_fixa": "Renda Fixa",
    "tesouro": "Tesouro",
}


def _brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _pct_str(value: Decimal | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value >= Decimal("0") else ""
    raw = f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}{'' if value >= Decimal('0') else '-'}{raw}%"


def _abs_change_str(value: Decimal | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value >= Decimal("0") else ""
    return sign + _brl(value)


def _section(title: str) -> str:
    return f"\n## {title}\n"


_CLASS_LABELS = {
    "acao": "Ações",
    "etf": "ETFs",
    "fundo_fii": "FIIs",
    "fundo": "Fundos",
    "renda_fixa": "Renda Fixa",
    "tesouro": "Tesouro Direto",
}


def _format_overall_performance(op: OverallPerformance, has_mov: bool) -> str:
    lines: list[str] = []

    lines.append(f"**Patrimônio Atual:** {_brl(op.total_current)}  ")
    if op.total_cost is not None:
        lines.append(f"**Custo Total Investido:** {_brl(op.total_cost)}  ")
        ret_str = _abs_change_str(op.total_return)
        pct_str = _pct_str(op.total_return_pct)
        lines.append(f"**Retorno:** {ret_str} ({pct_str})")
    else:
        lines.append(
            "**Custo Total Investido:** —  \n"
            "> **Nota:** Sem dados de movimentação — custo e retorno indisponíveis "
            "para ações, ETFs e fundos. "
            "Use `import YEAR --movimentacao PATH` para habilitar."
        )

    if not has_mov:
        lines.append(
            "\n> **Nota:** Retornos parciais — apenas Tesouro Direto tem custo "
            "disponível sem movimentação."
        )

    lines.append("")
    lines.append("| Classe | Valor Atual | Custo Total | Retorno Abs | Retorno % |")
    lines.append("|--------|-------------|-------------|-------------|-----------|")

    total_current = Decimal("0")
    total_cost_known = Decimal("0")
    has_any_cost = False

    for cp in op.by_class:
        label = _CLASS_LABELS.get(cp.asset_class, cp.asset_class)
        cb_str = _brl(cp.cost_basis) if cp.cost_basis is not None else "—"
        lines.append(
            f"| {label}"
            f" | {_brl(cp.current_value)}"
            f" | {cb_str}"
            f" | {_abs_change_str(cp.total_return)}"
            f" | {_pct_str(cp.total_return_pct)}"
            " |"
        )
        total_current += cp.current_value
        if cp.cost_basis is not None:
            total_cost_known += cp.cost_basis
            has_any_cost = True

    total_cost_str = _brl(total_cost_known) if has_any_cost else "—"
    total_ret = (total_current - total_cost_known) if has_any_cost else None
    total_ret_pct = (
        (total_ret / total_cost_known * Decimal("100")).quantize(Decimal("0.01"))
        if total_ret is not None and total_cost_known != Decimal("0")
        else None
    )
    lines.append(
        f"| **Total**"
        f" | **{_brl(total_current)}**"
        f" | **{total_cost_str}**"
        f" | **{_abs_change_str(total_ret)}**"
        f" | **{_pct_str(total_ret_pct)}**"
        " |"
    )
    return "\n".join(lines)


def _format_performance(performance: list[AssetPerformance], has_mov: bool) -> str:
    lines: list[str] = []
    if not has_mov:
        lines.append(
            "> **Nota:** Nenhum dado de movimentação importado. "
            "Custo médio e retorno indisponíveis. "
            "Use `import YEAR --movimentacao PATH` para habilitar.\n"
        )
    lines.append(
        "| Ticker | Classe | Valor Atual | Custo Total | Retorno Abs | Retorno % |"
    )
    lines.append(
        "|--------|--------|-------------|-------------|-------------|-----------|"
    )
    for p in performance:
        label = _ASSET_CLASS_LABELS.get(p.asset_class, p.asset_class)
        lines.append(
            f"| {p.ticker}"
            f" | {label}"
            f" | {_brl(p.current_value)}"
            f" | {_brl(p.cost_basis) if p.cost_basis is not None else '—'}"
            f" | {_abs_change_str(p.total_return)}"
            f" | {_pct_str(p.total_return_pct)}"
            " |"
        )
    return "\n".join(lines)


def _format_allocation(alloc: AllocationBreakdown) -> str:
    rows = [
        ("Ações", alloc.acoes, alloc.pct_acoes),
        ("FIIs", alloc.fiis, alloc.pct_fiis),
        ("Fundos", alloc.fundos, alloc.pct_fundos),
        ("ETFs", alloc.etfs, alloc.pct_etfs),
        ("Renda Fixa", alloc.renda_fixa, alloc.pct_renda_fixa),
        ("Tesouro Direto", alloc.tesouro, alloc.pct_tesouro),
    ]
    lines: list[str] = []
    lines.append("| Classe | Valor | % |")
    lines.append("|--------|-------|---|")
    for label, valor, pct in rows:
        raw_pct = f"{pct:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        lines.append(f"| {label} | {_brl(valor)} | {raw_pct}% |")
    lines.append(f"| **Total** | **{_brl(alloc.total)}** | 100,00% |")
    return "\n".join(lines)


def _format_dividend_yields(yields: list[DividendYield], year: int) -> str:
    lines: list[str] = []
    lines.append(
        f"> Proventos creditados na carteira em {year} "
        "(dividendos, JCP, rendimentos FII).\n"
    )
    lines.append("| Ticker | Proventos (ano) | Valor Posição | Yield % |")
    lines.append("|--------|-----------------|---------------|---------|")
    total = Decimal("0")
    for y in yields:
        raw_pct = (
            f"{y.yield_pct:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            + "%"
            if y.yield_pct is not None
            else "—"
        )
        lines.append(
            f"| {y.ticker}"
            f" | {_brl(y.proventos_ano)}"
            f" | {_brl(y.current_value) if y.current_value != Decimal('0') else '—'}"
            f" | {raw_pct}"
            " |"
        )
        total += y.proventos_ano
    lines.append(f"| **TOTAL** | **{_brl(total)}** | | |")
    return "\n".join(lines)


def _format_cost_basis(entries: list[CostBasisEntry]) -> str:
    lines: list[str] = []
    lines.append("| Ticker | Preço Médio | Quantidade | Custo Total |")
    lines.append("|--------|-------------|------------|-------------|")
    for e in entries:
        qty_str = (
            f"{e.quantity:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        lines.append(
            f"| {e.ticker}"
            f" | {_brl(e.avg_price)}"
            f" | {qty_str}"
            f" | {_brl(e.total_cost)}"
            " |"
        )
    return "\n".join(lines)


def format_analytics_report(report: AnalyticsReport, db_label: str) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    lines: list[str] = []
    lines.append("# Relatório de Analytics da Carteira — gerado por contabilidade")
    lines.append("")
    lines.append(f"**Banco:** `{db_label}`  ")
    lines.append(f"**Ano de referência:** {report.year}  ")
    lines.append(f"**Data de geração:** {now}")
    lines.append("")

    lines.append(_section("PERFORMANCE GERAL DA CARTEIRA"))
    lines.append(
        _format_overall_performance(report.overall_performance, report.has_movimentacao)
    )
    lines.append("")

    lines.append(_section("DESEMPENHO POR ATIVO"))
    lines.append(_format_performance(report.performance, report.has_movimentacao))
    lines.append("")

    lines.append(_section(f"ALOCAÇÃO POR CLASSE — {report.year} (FII separado)"))
    lines.append(_format_allocation(report.allocation))
    lines.append("")

    lines.append(_section(f"DIVIDEND YIELD POR POSIÇÃO — {report.year}"))
    lines.append(_format_dividend_yields(report.dividend_yields, report.year))
    lines.append("")

    lines.append(_section("CUSTO MÉDIO POR ATIVO"))
    if not report.has_movimentacao:
        lines.append(
            "> **Nota:** Nenhum dado de movimentação importado. "
            "Use `import YEAR --movimentacao PATH` para habilitar esta seção.\n"
        )
    else:
        lines.append(_format_cost_basis(report.cost_basis))
    lines.append("")

    return "\n".join(lines)
