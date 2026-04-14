# pylint: disable=duplicate-code
import sqlite3
from dataclasses import dataclass
from decimal import Decimal

from contabilidade.db.b3_repository import load_b3_report
from contabilidade.db.import_log import has_movimentacao
from contabilidade.db.movimentacao_repository import load_movimentacao_report
from contabilidade.models.analytics import (
    AllocationBreakdown,
    AnalyticsReport,
    AssetPerformance,
    ClassPerformance,
    CostBasisEntry,
    DividendYield,
    OverallPerformance,
)
from contabilidade.models.b3 import B3Report
from contabilidade.models.movimentacao import MovimentacaoRow

# pylint: disable=duplicate-code
_COMPRA_EVENTOS = {"Transferência - Liquidação", "Compra", "COMPRA / VENDA"}
_VENDA_EVENTOS = {
    "Transferência - Liquidação",
    "COMPRA / VENDA",
    "VENCIMENTO",
    "Resgate",
}


def _ticker_from_produto(produto: str) -> tuple[str, str]:
    if " - " in produto:
        parts = produto.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return produto.strip(), produto.strip()


def _is_fii(produto: str) -> bool:
    upper = produto.upper()
    return "IMOB" in upper or "FII" in upper or "FIAGRO" in upper


# pylint: enable=duplicate-code


@dataclass
class _CostBasis:
    avg: Decimal
    qty: Decimal


def _sort_key(row: MovimentacaoRow) -> str:
    parts = row.data.split("/")
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return row.data


def _build_cost_basis(rows: list[MovimentacaoRow]) -> dict[str, _CostBasis]:
    cost_basis: dict[str, _CostBasis] = {}
    for row in sorted(rows, key=_sort_key):
        ticker, _ = _ticker_from_produto(row.produto)
        mov = row.movimentacao

        if row.entrada_saida == "Credito" and mov in _COMPRA_EVENTOS:
            qty = row.quantidade
            price = row.preco_unitario
            if qty is not None and price is not None and qty > Decimal("0"):
                if ticker in cost_basis:
                    cb = cost_basis[ticker]
                    new_qty = cb.qty + qty
                    new_avg = (cb.avg * cb.qty + price * qty) / new_qty
                    cost_basis[ticker] = _CostBasis(avg=new_avg, qty=new_qty)
                else:
                    cost_basis[ticker] = _CostBasis(avg=price, qty=qty)

        elif row.entrada_saida == "Debito" and mov in _VENDA_EVENTOS:
            qty = row.quantidade
            cb_sell = cost_basis.get(ticker)
            if cb_sell is not None and qty is not None and qty > Decimal("0"):
                new_qty = cb_sell.qty - qty
                if new_qty <= Decimal("0"):
                    del cost_basis[ticker]
                else:
                    cost_basis[ticker] = _CostBasis(avg=cb_sell.avg, qty=new_qty)

    return cost_basis


def _pct(part: Decimal, total: Decimal) -> Decimal:
    if total == Decimal("0"):
        return Decimal("0")
    return (part / total * Decimal("100")).quantize(Decimal("0.01"))


def _build_performance(
    b3: B3Report, cost_basis: dict[str, _CostBasis]
) -> list[AssetPerformance]:
    result: list[AssetPerformance] = []

    for a in b3.acoes:
        ticker = a.codigo_negociacao
        cb = cost_basis.get(ticker)
        cb_total = (
            (cb.avg * cb.qty).quantize(Decimal("0.01")) if cb is not None else None
        )
        ret = (a.valor_atualizado - cb_total) if cb_total is not None else None
        ret_pct = (
            (ret / cb_total * Decimal("100")).quantize(Decimal("0.01"))
            if ret is not None and cb_total is not None and cb_total != Decimal("0")
            else None
        )
        result.append(
            AssetPerformance(
                ticker=ticker,
                nome=a.produto,
                asset_class="acao",
                current_value=a.valor_atualizado,
                cost_basis=cb_total,
                total_return=ret,
                total_return_pct=ret_pct,
            )
        )

    for e in b3.etfs:
        ticker = e.codigo_negociacao
        cb = cost_basis.get(ticker)
        cb_total = (
            (cb.avg * cb.qty).quantize(Decimal("0.01")) if cb is not None else None
        )
        ret = (e.valor_atualizado - cb_total) if cb_total is not None else None
        ret_pct = (
            (ret / cb_total * Decimal("100")).quantize(Decimal("0.01"))
            if ret is not None and cb_total is not None and cb_total != Decimal("0")
            else None
        )
        result.append(
            AssetPerformance(
                ticker=ticker,
                nome=e.produto,
                asset_class="etf",
                current_value=e.valor_atualizado,
                cost_basis=cb_total,
                total_return=ret,
                total_return_pct=ret_pct,
            )
        )

    for f in b3.fundos:
        ticker, nome = _ticker_from_produto(f.produto)
        asset_class = "fundo_fii" if _is_fii(f.produto) else "fundo"
        cb = cost_basis.get(ticker)
        cb_total = (
            (cb.avg * cb.qty).quantize(Decimal("0.01")) if cb is not None else None
        )
        ret = (f.valor_atualizado - cb_total) if cb_total is not None else None
        ret_pct = (
            (ret / cb_total * Decimal("100")).quantize(Decimal("0.01"))
            if ret is not None and cb_total is not None and cb_total != Decimal("0")
            else None
        )
        result.append(
            AssetPerformance(
                ticker=ticker,
                nome=nome,
                asset_class=asset_class,
                current_value=f.valor_atualizado,
                cost_basis=cb_total,
                total_return=ret,
                total_return_pct=ret_pct,
            )
        )

    for r in b3.renda_fixa:
        result.append(
            AssetPerformance(
                ticker=r.codigo,
                nome=r.produto,
                asset_class="renda_fixa",
                current_value=r.valor_atualizado_curva,
                cost_basis=None,
                total_return=None,
                total_return_pct=None,
            )
        )

    for t in b3.tesouro_direto:
        cb_total = t.valor_aplicado
        ret = t.valor_atualizado - cb_total
        ret_pct = (
            (ret / cb_total * Decimal("100")).quantize(Decimal("0.01"))
            if cb_total != Decimal("0")
            else None
        )
        result.append(
            AssetPerformance(
                ticker=t.produto,
                nome=t.produto,
                asset_class="tesouro",
                current_value=t.valor_atualizado,
                cost_basis=cb_total,
                total_return=ret,
                total_return_pct=ret_pct,
            )
        )

    return sorted(result, key=lambda p: p.current_value, reverse=True)


def _build_dividend_yields(b3: B3Report) -> list[DividendYield]:
    # Sum proventos per ticker
    totals: dict[str, Decimal] = {}
    nomes: dict[str, str] = {}
    for prov in b3.proventos:
        ticker, nome = _ticker_from_produto(prov.produto)
        totals[ticker] = totals.get(ticker, Decimal("0")) + prov.valor_liquido
        nomes[ticker] = nome

    # Build position value lookup
    position_values: dict[str, Decimal] = {}
    for a in b3.acoes:
        position_values[a.codigo_negociacao] = (
            position_values.get(a.codigo_negociacao, Decimal("0")) + a.valor_atualizado
        )
    for e in b3.etfs:
        position_values[e.codigo_negociacao] = (
            position_values.get(e.codigo_negociacao, Decimal("0")) + e.valor_atualizado
        )
    for f in b3.fundos:
        ticker, _ = _ticker_from_produto(f.produto)
        position_values[ticker] = (
            position_values.get(ticker, Decimal("0")) + f.valor_atualizado
        )

    yields: list[DividendYield] = []
    for ticker, proventos_ano in totals.items():
        current_value = position_values.get(ticker, Decimal("0"))
        yield_pct = (
            (proventos_ano / current_value * Decimal("100")).quantize(Decimal("0.01"))
            if current_value != Decimal("0")
            else None
        )
        yields.append(
            DividendYield(
                ticker=ticker,
                nome=nomes[ticker],
                proventos_ano=proventos_ano,
                current_value=current_value,
                yield_pct=yield_pct,
            )
        )

    return sorted(
        yields,
        key=lambda y: (y.yield_pct is None, -(y.yield_pct or Decimal("0"))),
    )


def _build_allocation(b3: B3Report) -> AllocationBreakdown:
    acoes = sum((a.valor_atualizado for a in b3.acoes), Decimal("0"))
    etfs = sum((e.valor_atualizado for e in b3.etfs), Decimal("0"))
    fiis = sum(
        (f.valor_atualizado for f in b3.fundos if _is_fii(f.produto)), Decimal("0")
    )
    fundos = sum(
        (f.valor_atualizado for f in b3.fundos if not _is_fii(f.produto)), Decimal("0")
    )
    renda_fixa = sum((r.valor_atualizado_curva for r in b3.renda_fixa), Decimal("0"))
    tesouro = sum((t.valor_atualizado for t in b3.tesouro_direto), Decimal("0"))
    total = acoes + etfs + fiis + fundos + renda_fixa + tesouro
    return AllocationBreakdown(
        year=b3.year,
        acoes=acoes,
        fiis=fiis,
        fundos=fundos,
        etfs=etfs,
        renda_fixa=renda_fixa,
        tesouro=tesouro,
        total=total,
        pct_acoes=_pct(acoes, total),
        pct_fiis=_pct(fiis, total),
        pct_fundos=_pct(fundos, total),
        pct_etfs=_pct(etfs, total),
        pct_renda_fixa=_pct(renda_fixa, total),
        pct_tesouro=_pct(tesouro, total),
    )


def _build_cost_basis_entries(
    cost_basis: dict[str, _CostBasis],
) -> list[CostBasisEntry]:
    entries: list[CostBasisEntry] = []
    for ticker, cb in cost_basis.items():
        entries.append(
            CostBasisEntry(
                ticker=ticker,
                nome=ticker,
                avg_price=cb.avg.quantize(Decimal("0.01")),
                quantity=cb.qty,
                total_cost=(cb.avg * cb.qty).quantize(Decimal("0.01")),
            )
        )
    return sorted(entries, key=lambda e: e.total_cost, reverse=True)


_CLASS_ORDER = ["acao", "etf", "fundo_fii", "fundo", "renda_fixa", "tesouro"]


def _build_overall_performance(
    performance: list[AssetPerformance],
) -> OverallPerformance:
    totals_current: dict[str, Decimal] = {}
    totals_cost: dict[str, Decimal] = {}

    for p in performance:
        totals_current[p.asset_class] = (
            totals_current.get(p.asset_class, Decimal("0")) + p.current_value
        )
        if p.cost_basis is not None:
            totals_cost[p.asset_class] = (
                totals_cost.get(p.asset_class, Decimal("0")) + p.cost_basis
            )

    by_class: list[ClassPerformance] = []
    for cls in _CLASS_ORDER:
        current = totals_current.get(cls, Decimal("0"))
        if current == Decimal("0") and cls not in totals_cost:
            continue
        cb = totals_cost.get(cls)
        ret = (current - cb) if cb is not None else None
        ret_pct = (
            (ret / cb * Decimal("100")).quantize(Decimal("0.01"))
            if ret is not None and cb is not None and cb != Decimal("0")
            else None
        )
        by_class.append(
            ClassPerformance(
                asset_class=cls,
                current_value=current,
                cost_basis=cb,
                total_return=ret,
                total_return_pct=ret_pct,
            )
        )

    total_current = sum((p.current_value for p in performance), Decimal("0"))
    total_cost: Decimal | None = (
        sum(totals_cost.values(), Decimal("0")) if totals_cost else None
    )
    total_return: Decimal | None = (
        (total_current - total_cost) if total_cost is not None else None
    )
    total_return_pct: Decimal | None = (
        (total_return / total_cost * Decimal("100")).quantize(Decimal("0.01"))
        if total_return is not None
        and total_cost is not None
        and total_cost != Decimal("0")
        else None
    )
    return OverallPerformance(
        total_current=total_current,
        total_cost=total_cost,
        total_return=total_return,
        total_return_pct=total_return_pct,
        by_class=by_class,
    )


def build_analytics_report(
    conn: sqlite3.Connection,
    b3_years: list[int],
) -> AnalyticsReport:
    latest_year = max(b3_years)
    b3 = load_b3_report(conn, latest_year)
    if b3 is None:
        raise ValueError(f"Dados do ano {latest_year} não encontrados no banco.")

    all_rows: list[MovimentacaoRow] = []
    has_mov = False
    for year in sorted(b3_years):
        if not has_movimentacao(conn, year):
            continue
        has_mov = True
        mov = load_movimentacao_report(conn, year)
        if mov is not None:
            all_rows.extend(mov.rows)

    cost_basis = _build_cost_basis(all_rows) if all_rows else {}
    performance = _build_performance(b3, cost_basis)

    return AnalyticsReport(
        year=latest_year,
        has_movimentacao=has_mov,
        overall_performance=_build_overall_performance(performance),
        performance=performance,
        dividend_yields=_build_dividend_yields(b3),
        cost_basis=_build_cost_basis_entries(cost_basis),
        allocation=_build_allocation(b3),
    )
