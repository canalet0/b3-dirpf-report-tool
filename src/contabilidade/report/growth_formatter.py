from datetime import datetime
from decimal import Decimal

from contabilidade.models.growth import GrowthReport, YearGrowth, YearSnapshot


def _brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _section(title: str) -> str:
    return f"\n## {title}\n"


def _format_pct_change(pct: Decimal | None) -> str:
    if pct is None:
        return "—"
    sign = "+" if pct >= Decimal("0") else ""
    raw = f"{abs(pct):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}{'' if pct >= Decimal('0') else '-'}{raw}%"


def _format_abs_change(val: Decimal | None) -> str:
    if val is None:
        return "—"
    sign = "+" if val >= Decimal("0") else ""
    return sign + _brl(val)


def _format_evolucao(snapshots: list[YearSnapshot], growth: list[YearGrowth]) -> str:
    lines: list[str] = []
    lines.append(
        "| Ano | Ações | ETFs | Fundos | Renda Fixa | Tesouro | **Total** | Var. Abs. | Var. % |"
    )
    lines.append(
        "|-----|-------|------|--------|------------|---------|-----------|-----------|--------|"
    )
    for snap, g in zip(snapshots, growth):
        lines.append(
            f"| {snap.year}"
            f" | {_brl(snap.acoes)}"
            f" | {_brl(snap.etfs)}"
            f" | {_brl(snap.fundos)}"
            f" | {_brl(snap.renda_fixa)}"
            f" | {_brl(snap.tesouro)}"
            f" | **{_brl(snap.total)}**"
            f" | {_format_abs_change(g.abs_change)}"
            f" | {_format_pct_change(g.pct_change)}"
            " |"
        )
    return "\n".join(lines)


def _format_alocacao(growth: list[YearGrowth]) -> str:
    lines: list[str] = []
    lines.append("| Ano | Ações | ETFs | Fundos | Renda Fixa | Tesouro |")
    lines.append("|-----|-------|------|--------|------------|---------|")
    for g in growth:

        def _p(v: Decimal) -> str:
            raw = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{raw}%"

        lines.append(
            f"| {g.year}"
            f" | {_p(g.pct_acoes)}"
            f" | {_p(g.pct_etfs)}"
            f" | {_p(g.pct_fundos)}"
            f" | {_p(g.pct_renda_fixa)}"
            f" | {_p(g.pct_tesouro)}"
            " |"
        )
    return "\n".join(lines)


def _format_proventos(snapshots: list[YearSnapshot]) -> str:
    lines: list[str] = []
    lines.append("| Ano | Dividendos/FII/JCP | Reembolsos (BTC) | Total Renda |")
    lines.append("|-----|--------------------|--------------------|-------------|")
    total_prov = Decimal("0")
    total_remb = Decimal("0")
    total_inc = Decimal("0")
    for snap in snapshots:
        lines.append(
            f"| {snap.year}"
            f" | {_brl(snap.proventos)}"
            f" | {_brl(snap.reembolsos)}"
            f" | {_brl(snap.total_income)}"
            " |"
        )
        total_prov += snap.proventos
        total_remb += snap.reembolsos
        total_inc += snap.total_income
    lines.append(
        f"| **TOTAL**"
        f" | **{_brl(total_prov)}**"
        f" | **{_brl(total_remb)}**"
        f" | **{_brl(total_inc)}**"
        " |"
    )
    return "\n".join(lines)


def _format_monthly_income(report: GrowthReport) -> str:
    if not report.has_movimentacao:
        return (
            "\n> **Nota:** Nenhum dado de movimentação importado. "
            "Use `import YEAR --movimentacao PATH` para habilitar esta seção.\n"
        )

    lines: list[str] = []
    if not report.monthly_income:
        lines.append(
            "\n> Movimentação importada mas nenhuma renda creditada encontrada.\n"
        )
        return "\n".join(lines)

    lines.append(
        "> **Nota:** Valores de créditos de Dividendo, JCP, Rendimento e Reembolso "
        "extraídos da movimentação importada. Anos sem movimentação não aparecem aqui.\n"
    )
    lines.append("| Mês | Renda Recebida |")
    lines.append("|-----|----------------|")
    total = Decimal("0")
    for entry in report.monthly_income:
        lines.append(f"| {entry.month} | {_brl(entry.valor)} |")
        total += entry.valor
    lines.append(f"| **TOTAL** | **{_brl(total)}** |")
    return "\n".join(lines)


def format_growth_report(report: GrowthReport, db_label: str) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    available = ", ".join(str(s.year) for s in report.years)

    lines: list[str] = []
    lines.append("# Relatório de Crescimento da Carteira — gerado por contabilidade")
    lines.append("")
    lines.append(f"**Banco:** `{db_label}`  ")
    lines.append(f"**Anos disponíveis:** {available}  ")
    lines.append(f"**Data de geração:** {now}")
    lines.append("")

    lines.append(_section("EVOLUÇÃO ANUAL DO PATRIMÔNIO"))
    lines.append(_format_evolucao(report.years, report.growth))
    lines.append("")

    lines.append(_section("ALOCAÇÃO POR CLASSE DE ATIVO (% do total)"))
    lines.append(_format_alocacao(report.growth))
    lines.append("")

    lines.append(_section("PROVENTOS E REEMBOLSOS POR ANO"))
    lines.append(_format_proventos(report.years))
    lines.append("")

    lines.append(_section("RENDA MENSAL (MOVIMENTAÇÃO)"))
    lines.append(_format_monthly_income(report))
    lines.append("")

    return "\n".join(lines)
