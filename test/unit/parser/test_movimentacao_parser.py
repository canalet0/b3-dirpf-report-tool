from decimal import Decimal
from typing import cast

from contabilidade.parser.movimentacao_parser import (
    _parse_movimentacao,
    _to_optional_decimal,
)

Rows = list[list[str | None]]


def _r(rows: list[list[str]]) -> Rows:
    return cast(Rows, rows)


_HEADER = [
    "Entrada/Saída",
    "Data",
    "Movimentação",
    "Produto",
    "Instituição",
    "Quantidade",
    "Preço unitário",
    "Valor da Operação",
]


def _row(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    entrada: str = "Credito",
    data: str = "01/01/2024",
    mov: str = "Dividendo",
    produto: str = "ITSA4 - ITAUSA",
    inst: str = "INTER",
    qty: str = "10",
    preco: str = "1.50",
    valor: str = "15.00",
) -> list[str]:
    return [entrada, data, mov, produto, inst, qty, preco, valor]


def test_to_optional_decimal_dash_returns_none() -> None:
    assert _to_optional_decimal("-") is None


def test_to_optional_decimal_none_returns_none() -> None:
    assert _to_optional_decimal(None) is None


def test_to_optional_decimal_empty_returns_none() -> None:
    assert _to_optional_decimal("") is None


def test_to_optional_decimal_integer() -> None:
    assert _to_optional_decimal("10") == Decimal("10")


def test_to_optional_decimal_dot_decimal() -> None:
    assert _to_optional_decimal("85.33") == Decimal("85.33")


def test_to_optional_decimal_comma_decimal() -> None:
    assert _to_optional_decimal("1270,19") == Decimal("1270.19")


def test_to_optional_decimal_br_format() -> None:
    assert _to_optional_decimal("1.270,19") == Decimal("1270.19")


def test_parse_movimentacao_skips_header() -> None:
    rows = _r([_HEADER, _row()])
    result = _parse_movimentacao(rows)
    assert len(result) == 1


def test_parse_movimentacao_dash_qty_is_none() -> None:
    rows = _r([_HEADER, _row(qty="-")])
    result = _parse_movimentacao(rows)
    assert result[0].quantidade is None


def test_parse_movimentacao_dash_preco_is_none() -> None:
    rows = _r([_HEADER, _row(preco="-")])
    result = _parse_movimentacao(rows)
    assert result[0].preco_unitario is None


def test_parse_movimentacao_dash_valor_is_none() -> None:
    rows = _r([_HEADER, _row(valor="-")])
    result = _parse_movimentacao(rows)
    assert result[0].valor_operacao is None


def test_parse_movimentacao_fields_populated() -> None:
    rows = _r(
        [
            _HEADER,
            _row(
                entrada="Debito",
                data="29/11/2022",
                mov="Transferência - Liquidação",
                produto="BERK34 - BERKSHIRE",
                inst="INTER",
                qty="5",
                preco="85.33",
                valor="426.65",
            ),
        ]
    )
    result = _parse_movimentacao(rows)
    r = result[0]
    assert r.entrada_saida == "Debito"
    assert r.data == "29/11/2022"
    assert r.movimentacao == "Transferência - Liquidação"
    assert r.produto == "BERK34 - BERKSHIRE"
    assert r.quantidade == Decimal("5")
    assert r.preco_unitario == Decimal("85.33")
    assert r.valor_operacao == Decimal("426.65")


def test_parse_movimentacao_skips_short_rows() -> None:
    rows = _r([_HEADER, ["Credito", "01/01/2024"]])
    result = _parse_movimentacao(rows)
    assert not result


def test_parse_movimentacao_skips_empty_entrada() -> None:
    rows = _r(
        [_HEADER, ["", "01/01/2024", "Dividendo", "ITSA4", "INTER", "1", "1", "1"]]
    )
    result = _parse_movimentacao(rows)
    assert not result
