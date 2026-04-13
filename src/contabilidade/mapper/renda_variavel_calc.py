from dataclasses import dataclass
from decimal import Decimal

from contabilidade.mapper._income_categories import classify_provento
from contabilidade.models.dirpf import (
    EventoCorporativo,
    OperacaoRendaVariavel,
    ResumoMensalRendaVariavel,
)
from contabilidade.models.movimentacao import MovimentacaoRow

_COMPRA_EVENTOS = {"Transferência - Liquidação", "Compra", "COMPRA / VENDA"}
_VENDA_EVENTOS = {
    "Transferência - Liquidação",
    "COMPRA / VENDA",
    "VENCIMENTO",
    "Resgate",
}
_INCOME_EVENTOS = {
    "Dividendo",
    "Juros Sobre Capital Próprio",
    "Rendimento",
    "Reembolso",
}
_CORPORATIVO_EVENTOS = {
    "Bonificação em Ativos",
    "Desdobro",
    "Grupamento",
    "Direito de Subscrição",
    "Direitos de Subscrição - Não Exercido",
    "Cessão de Direitos",
    "Cessão de Direitos - Solicitada",
    "Atualização",
    "Fração em Ativos",
    "Leilão de Fração",
    "Transferência",
}

_MONTH_PT = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Março",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro",
}

_ISENCAO_THRESHOLD = Decimal("20000")


@dataclass
class _CostBasis:
    avg: Decimal
    qty: Decimal


def _ticker_from_produto(produto: str) -> tuple[str, str]:
    if " - " in produto:
        parts = produto.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return produto.strip(), produto.strip()


def _date_to_month(data: str) -> str:
    """Convert "DD/MM/YYYY" to "YYYY-MM"."""
    parts = data.split("/")
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}"
    return data


def _month_label(mes: str) -> str:
    """Convert "YYYY-MM" to "Mês/YYYY"."""
    parts = mes.split("-")
    if len(parts) == 2:
        nome = _MONTH_PT.get(parts[1], parts[1])
        return f"{nome}/{parts[0]}"
    return mes


def compute_renda_variavel(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    rows: list[MovimentacaoRow],
) -> tuple[list[ResumoMensalRendaVariavel], list[EventoCorporativo]]:
    # Sort chronologically (DD/MM/YYYY → sortable via YYYY-MM-DD)
    def sort_key(r: MovimentacaoRow) -> str:
        parts = r.data.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return r.data

    sorted_rows = sorted(rows, key=sort_key)

    cost_basis: dict[str, _CostBasis] = {}
    operacoes_by_month: dict[str, list[OperacaoRendaVariavel]] = {}
    corporativos: list[EventoCorporativo] = []

    for row in sorted_rows:
        ticker, nome = _ticker_from_produto(row.produto)
        mes = _date_to_month(row.data)
        mov = row.movimentacao

        if row.entrada_saida == "Credito" and mov in _COMPRA_EVENTOS:
            # Buy: update cost basis
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

            op = OperacaoRendaVariavel(
                mes=mes,
                ticker=ticker,
                nome=nome,
                tipo="Compra",
                data=row.data,
                quantidade=qty if qty is not None else Decimal("0"),
                preco_unitario=price,
                valor_operacao=row.valor_operacao,
                custo_medio=None,
                ganho_estimado=None,
            )
            operacoes_by_month.setdefault(mes, []).append(op)

        elif row.entrada_saida == "Debito" and mov in _VENDA_EVENTOS:
            # Sell: compute gain if possible
            qty = row.quantidade
            price = row.preco_unitario
            valor = row.valor_operacao
            cb_sell: _CostBasis | None = cost_basis.get(ticker)
            custo_medio = cb_sell.avg if cb_sell is not None else None

            ganho: Decimal | None = None
            if price is not None and custo_medio is not None and qty is not None:
                ganho = (price - custo_medio) * qty
            elif valor is not None and custo_medio is not None and qty is not None:
                ganho = valor - custo_medio * qty

            # Decrement cost basis
            if cb_sell is not None and qty is not None and qty > Decimal("0"):
                new_qty = cb_sell.qty - qty
                if new_qty <= Decimal("0"):
                    del cost_basis[ticker]
                else:
                    cost_basis[ticker] = _CostBasis(avg=cb_sell.avg, qty=new_qty)

            op = OperacaoRendaVariavel(
                mes=mes,
                ticker=ticker,
                nome=nome,
                tipo="Venda",
                data=row.data,
                quantidade=qty if qty is not None else Decimal("0"),
                preco_unitario=price,
                valor_operacao=valor,
                custo_medio=custo_medio,
                ganho_estimado=ganho,
            )
            operacoes_by_month.setdefault(mes, []).append(op)

        elif mov in _CORPORATIVO_EVENTOS:
            obs = _corporativo_obs(mov, ticker)
            corporativos.append(
                EventoCorporativo(
                    data=row.data,
                    ticker=ticker,
                    nome=nome,
                    tipo=mov,
                    quantidade=row.quantidade,
                    observacao=obs,
                )
            )

    # Build monthly summaries (only months with sells)
    summaries: list[ResumoMensalRendaVariavel] = []
    for mes in sorted(operacoes_by_month.keys()):
        ops = operacoes_by_month[mes]
        vendas = [o for o in ops if o.tipo == "Venda"]
        if not vendas:
            continue

        any_missing_price = any(
            o.valor_operacao is None and o.preco_unitario is None for o in vendas
        )

        if any_missing_price:
            total_vendas = None
            total_ganho = None
            isento = None
        else:
            total_vendas = sum(
                [o.valor_operacao or Decimal("0") for o in vendas], Decimal("0")
            )
            ganhos = [o.ganho_estimado for o in vendas]
            if all(g is not None for g in ganhos):
                total_ganho = sum([g for g in ganhos if g is not None], Decimal("0"))
            else:
                total_ganho = None
            isento = total_vendas <= _ISENCAO_THRESHOLD

        tickers_vendidos = list(dict.fromkeys(o.ticker for o in vendas))

        summaries.append(
            ResumoMensalRendaVariavel(
                mes=mes,
                mes_label=_month_label(mes),
                total_vendas=total_vendas,
                total_ganho_estimado=total_ganho,
                isento=isento,
                tickers_vendidos=tickers_vendidos,
                operacoes=ops,
            )
        )

    return summaries, corporativos


def _corporativo_obs(tipo: str, ticker: str) -> str:
    obs_map = {
        "Bonificação em Ativos": (
            f"Bonificação recebida em {ticker}. "
            "Registrar custo de aquisição conforme informe da empresa."
        ),
        "Desdobro": (
            f"Desdobramento de ações de {ticker}. "
            "Reduzir o custo médio proporcionalmente."
        ),
        "Grupamento": (
            f"Grupamento de ações de {ticker}. "
            "Aumentar o custo médio proporcionalmente."
        ),
        "Direito de Subscrição": (
            f"Direito de subscrição recebido para {ticker}. "
            "Verifique se foi exercido ou cedido."
        ),
        "Direitos de Subscrição - Não Exercido": (
            f"Direito de subscrição não exercido para {ticker}."
        ),
        "Cessão de Direitos": (
            f"Cessão de direitos de {ticker}. Verificar tratamento fiscal."
        ),
        "Cessão de Direitos - Solicitada": (
            f"Cessão de direitos solicitada para {ticker}."
        ),
        "Atualização": (
            f"Atualização de posição em {ticker}. Verificar com informe da corretora."
        ),
        "Fração em Ativos": (
            f"Fração de ativos recebida em {ticker}. "
            "Verificar tratamento como rendimento ou ajuste de posição."
        ),
        "Leilão de Fração": (
            f"Leilão de fração de {ticker}. Pode gerar ganho/perda de capital."
        ),
        "Transferência": (
            f"Transferência de custódia de {ticker}. "
            "Não há evento tributável, mas verifique o custo médio."
        ),
    }
    return obs_map.get(tipo, f"Evento corporativo: {tipo} em {ticker}.")


def extract_income_from_movimentacao(rows: list[MovimentacaoRow]) -> dict[str, Decimal]:
    """Sum income (Credito) rows by category using classify_provento."""
    totals: dict[str, Decimal] = {}
    for row in rows:
        if row.entrada_saida != "Credito":
            continue
        if row.movimentacao not in _INCOME_EVENTOS:
            continue
        if row.valor_operacao is None:
            continue
        # Reembolso is a separate category matching the B3 reembolsos sheet
        if row.movimentacao == "Reembolso":
            category = "reembolso"
        else:
            category = classify_provento(row.movimentacao)
        totals[category] = totals.get(category, Decimal("0")) + row.valor_operacao
    return totals
