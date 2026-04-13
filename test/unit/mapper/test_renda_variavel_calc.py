from decimal import Decimal

from contabilidade.mapper.renda_variavel_calc import (
    compute_renda_variavel,
    extract_income_from_movimentacao,
)
from contabilidade.models.movimentacao import MovimentacaoRow


def _row(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    entrada: str = "Credito",
    data: str = "01/01/2024",
    mov: str = "Dividendo",
    produto: str = "ITSA4 - ITAUSA",
    qty: str | None = "10",
    preco: str | None = "1.00",
    valor: str | None = "10.00",
) -> MovimentacaoRow:
    return MovimentacaoRow(
        entrada_saida=entrada,
        data=data,
        movimentacao=mov,
        produto=produto,
        instituicao="INTER",
        quantidade=Decimal(qty) if qty is not None else None,
        preco_unitario=Decimal(preco) if preco is not None else None,
        valor_operacao=Decimal(valor) if valor is not None else None,
    )


def _buy(produto: str, data: str, qty: str, preco: str) -> MovimentacaoRow:
    valor = str(Decimal(qty) * Decimal(preco))
    return _row(
        "Credito", data, "Transferência - Liquidação", produto, qty, preco, valor
    )


def _sell(
    produto: str, data: str, qty: str, preco: str | None, valor: str | None
) -> MovimentacaoRow:
    return _row(
        "Debito", data, "Transferência - Liquidação", produto, qty, preco, valor
    )


# --- cost basis tests ---


def test_buy_only_no_sell_summaries() -> None:
    rows = [_buy("ITSA4 - ITAUSA", "01/01/2024", "10", "8.00")]
    summaries, corporativos = compute_renda_variavel(rows)
    assert not summaries
    assert not corporativos


def test_sell_after_buy_computes_gain() -> None:
    rows = [
        _buy("ITSA4 - ITAUSA", "01/01/2024", "10", "8.00"),
        _sell("ITSA4 - ITAUSA", "15/01/2024", "10", "10.00", "100.00"),
    ]
    summaries, _ = compute_renda_variavel(rows)
    assert len(summaries) == 1
    op_sell = [o for o in summaries[0].operacoes if o.tipo == "Venda"][0]
    assert op_sell.custo_medio == Decimal("8.00")
    assert op_sell.ganho_estimado == Decimal("20.00")  # (10 - 8) * 10


def test_weighted_average_cost() -> None:
    rows = [
        _buy("VALE3 - VALE", "01/01/2024", "10", "80.00"),
        _buy("VALE3 - VALE", "15/01/2024", "10", "100.00"),
        _sell("VALE3 - VALE", "20/02/2024", "5", "95.00", "475.00"),
    ]
    summaries, _ = compute_renda_variavel(rows)
    op_sell = [o for o in summaries[0].operacoes if o.tipo == "Venda"][0]
    # avg = (80*10 + 100*10) / 20 = 90.00
    assert op_sell.custo_medio == Decimal("90.00")
    assert op_sell.ganho_estimado == Decimal("25.00")  # (95 - 90) * 5


def test_sell_missing_price_no_gain() -> None:
    rows = [
        _buy("WEGE3 - WEG", "01/01/2024", "10", "50.00"),
        _sell("WEGE3 - WEG", "15/03/2024", "5", None, None),
    ]
    summaries, _ = compute_renda_variavel(rows)
    assert len(summaries) == 1
    op_sell = [o for o in summaries[0].operacoes if o.tipo == "Venda"][0]
    assert op_sell.ganho_estimado is None


def test_sell_missing_price_total_vendas_none() -> None:
    rows = [
        _buy("WEGE3 - WEG", "01/01/2024", "10", "50.00"),
        _sell("WEGE3 - WEG", "15/03/2024", "5", None, None),
    ]
    summaries, _ = compute_renda_variavel(rows)
    assert summaries[0].total_vendas is None
    assert summaries[0].isento is None


def test_isento_below_threshold() -> None:
    rows = [
        _buy("BERK34 - BERK", "01/01/2022", "5", "72.14"),
        _sell("BERK34 - BERK", "29/11/2022", "5", "85.33", "426.65"),
    ]
    summaries, _ = compute_renda_variavel(rows)
    assert summaries[0].isento is True
    assert summaries[0].total_vendas == Decimal("426.65")


def test_tributavel_above_threshold() -> None:
    rows = [
        _buy("VALE3 - VALE", "01/01/2024", "100", "100.00"),
        _sell("VALE3 - VALE", "15/06/2024", "100", "210.00", "21000.00"),
    ]
    summaries, _ = compute_renda_variavel(rows)
    assert summaries[0].isento is False


def test_corporativo_evento_captured() -> None:
    rows = [
        _row(
            "Credito",
            "22/12/2021",
            "Bonificação em Ativos",
            "ITSA4 - ITAUSA",
            "2",
            None,
            None,
        ),
    ]
    summaries, corporativos = compute_renda_variavel(rows)
    assert not summaries
    assert len(corporativos) == 1
    assert corporativos[0].tipo == "Bonificação em Ativos"
    assert corporativos[0].ticker == "ITSA4"


def test_multiple_months_separate_summaries() -> None:
    rows = [
        _buy("A - A", "01/01/2024", "10", "10.00"),
        _sell("A - A", "15/01/2024", "5", "12.00", "60.00"),
        _sell("A - A", "15/03/2024", "5", "14.00", "70.00"),
    ]
    summaries, _ = compute_renda_variavel(rows)
    assert len(summaries) == 2
    months = [s.mes for s in summaries]
    assert "2024-01" in months
    assert "2024-03" in months


# --- extract_income_from_movimentacao ---


def test_extract_income_dividendo() -> None:
    rows = [_row("Credito", mov="Dividendo", valor="41.16")]
    result = extract_income_from_movimentacao(rows)
    assert result.get("dividendo") == Decimal("41.16")


def test_extract_income_jcp() -> None:
    rows = [_row("Credito", mov="Juros Sobre Capital Próprio", valor="9.92")]
    result = extract_income_from_movimentacao(rows)
    assert result.get("jcp") == Decimal("9.92")


def test_extract_income_rendimento() -> None:
    rows = [_row("Credito", mov="Rendimento", valor="10.00")]
    result = extract_income_from_movimentacao(rows)
    assert result.get("rendimento_fii") == Decimal("10.00")


def test_extract_income_skips_debito() -> None:
    rows = [_row("Debito", mov="Dividendo", valor="5.00")]
    result = extract_income_from_movimentacao(rows)
    assert not result


def test_extract_income_skips_none_valor() -> None:
    rows = [_row("Credito", mov="Dividendo", valor=None)]
    result = extract_income_from_movimentacao(rows)
    assert not result


def test_extract_income_accumulates_same_category() -> None:
    rows = [
        _row("Credito", mov="Dividendo", valor="10.00"),
        _row("Credito", mov="Dividendo", valor="5.00"),
    ]
    result = extract_income_from_movimentacao(rows)
    assert result["dividendo"] == Decimal("15.00")
