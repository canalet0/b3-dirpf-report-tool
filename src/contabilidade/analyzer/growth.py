import sqlite3
from decimal import Decimal

from contabilidade.db.b3_repository import load_b3_report
from contabilidade.db.import_log import has_movimentacao
from contabilidade.db.movimentacao_repository import load_movimentacao_report
from contabilidade.models.b3 import B3Report
from contabilidade.models.growth import (
    GrowthReport,
    MonthlyIncome,
    YearGrowth,
    YearSnapshot,
)

_INCOME_EVENTOS = {  # pylint: disable=duplicate-code
    "Dividendo",
    "Juros Sobre Capital Próprio",
    "Rendimento",
    "Reembolso",
}


def _sum_acoes(b3: B3Report) -> Decimal:
    return sum((p.valor_atualizado for p in b3.acoes), Decimal("0"))


def _sum_etfs(b3: B3Report) -> Decimal:
    return sum((p.valor_atualizado for p in b3.etfs), Decimal("0"))


def _sum_fundos(b3: B3Report) -> Decimal:
    return sum((p.valor_atualizado for p in b3.fundos), Decimal("0"))


def _sum_renda_fixa(b3: B3Report) -> Decimal:
    return sum((p.valor_atualizado_curva for p in b3.renda_fixa), Decimal("0"))


def _sum_tesouro(b3: B3Report) -> Decimal:
    return sum((p.valor_atualizado for p in b3.tesouro_direto), Decimal("0"))


def _sum_proventos(b3: B3Report) -> Decimal:
    return sum((p.valor_liquido for p in b3.proventos), Decimal("0"))


def _sum_reembolsos(b3: B3Report) -> Decimal:
    return sum((p.valor_liquido for p in b3.reembolsos), Decimal("0"))


def _pct(part: Decimal, total: Decimal) -> Decimal:
    if total == Decimal("0"):
        return Decimal("0")
    return (part / total * Decimal("100")).quantize(Decimal("0.01"))


def _date_to_month(data: str) -> str:
    """Convert "DD/MM/YYYY" to "YYYY-MM"."""
    parts = data.split("/")
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}"
    return data


def _build_year_snapshot(year: int, b3: B3Report) -> YearSnapshot:
    acoes = _sum_acoes(b3)
    etfs = _sum_etfs(b3)
    fundos = _sum_fundos(b3)
    renda_fixa = _sum_renda_fixa(b3)
    tesouro = _sum_tesouro(b3)
    proventos = _sum_proventos(b3)
    reembolsos = _sum_reembolsos(b3)
    return YearSnapshot(
        year=year,
        acoes=acoes,
        etfs=etfs,
        fundos=fundos,
        renda_fixa=renda_fixa,
        tesouro=tesouro,
        total=acoes + etfs + fundos + renda_fixa + tesouro,
        proventos=proventos,
        reembolsos=reembolsos,
        total_income=proventos + reembolsos,
    )


def _build_year_growth(snap: YearSnapshot, prior: YearSnapshot | None) -> YearGrowth:
    if prior is None:
        abs_change = None
        pct_change = None
    else:
        abs_change = snap.total - prior.total
        pct_change = (
            ((abs_change / prior.total) * Decimal("100")).quantize(Decimal("0.01"))
            if prior.total != Decimal("0")
            else None
        )
    return YearGrowth(
        year=snap.year,
        total=snap.total,
        abs_change=abs_change,
        pct_change=pct_change,
        pct_acoes=_pct(snap.acoes, snap.total),
        pct_etfs=_pct(snap.etfs, snap.total),
        pct_fundos=_pct(snap.fundos, snap.total),
        pct_renda_fixa=_pct(snap.renda_fixa, snap.total),
        pct_tesouro=_pct(snap.tesouro, snap.total),
    )


def _build_monthly_income(  # pylint: disable=duplicate-code
    conn: sqlite3.Connection,
    years: list[int],
) -> tuple[list[MonthlyIncome], bool]:
    totals: dict[str, Decimal] = {}
    has_any = False

    for year in years:
        if not has_movimentacao(conn, year):
            continue
        has_any = True
        mov = load_movimentacao_report(conn, year)
        if mov is None:
            continue
        for row in mov.rows:
            if row.entrada_saida != "Credito":
                continue
            if row.movimentacao not in _INCOME_EVENTOS:
                continue
            if row.valor_operacao is None:
                continue
            month = _date_to_month(row.data)
            totals[month] = totals.get(month, Decimal("0")) + row.valor_operacao

    result = [MonthlyIncome(month=m, valor=v) for m, v in sorted(totals.items())]
    return result, has_any


def build_growth_report(
    conn: sqlite3.Connection,
    imported_years: list[int],
) -> GrowthReport:
    sorted_years = sorted(imported_years)
    snapshots = []
    for y in sorted_years:
        b3 = load_b3_report(conn, y)
        if b3 is None:
            raise ValueError(f"Dados do ano {y} não encontrados no banco.")
        snapshots.append(_build_year_snapshot(y, b3))
    growth = [
        _build_year_growth(snap, snapshots[i - 1] if i > 0 else None)
        for i, snap in enumerate(snapshots)
    ]
    monthly_income, has_mov = _build_monthly_income(conn, sorted_years)

    return GrowthReport(
        years=snapshots,
        growth=growth,
        monthly_income=monthly_income,
        has_movimentacao=has_mov,
    )
