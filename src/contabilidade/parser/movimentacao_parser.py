# pylint: disable=duplicate-code
from decimal import Decimal, InvalidOperation
from pathlib import Path

from contabilidade.models.movimentacao import MovimentacaoReport, MovimentacaoRow
from contabilidade.parser.xlsx_reader import read_xlsx

_SHEET = "Movimentação"


def _to_optional_decimal(value: str | None) -> Decimal | None:
    """Return None for missing/dash values instead of Decimal("0")."""
    if value is None or value.strip() in ("-", "", "None"):
        return None
    raw = value.strip()
    if "," in raw and "." in raw:
        cleaned = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        cleaned = raw.replace(",", ".")
    else:
        cleaned = raw
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _str(value: str | None) -> str:
    return value.strip() if value else ""


def _parse_movimentacao(rows: list[list[str | None]]) -> list[MovimentacaoRow]:
    result: list[MovimentacaoRow] = []
    for row in rows[1:]:  # skip header
        if len(row) < 8:
            continue
        if _str(row[0]) == "":
            continue
        result.append(
            MovimentacaoRow(
                entrada_saida=_str(row[0]),
                data=_str(row[1]),
                movimentacao=_str(row[2]),
                produto=_str(row[3]),
                instituicao=_str(row[4]),
                quantidade=_to_optional_decimal(row[5]),
                preco_unitario=_to_optional_decimal(row[6]),
                valor_operacao=_to_optional_decimal(row[7]),
            )
        )
    return result


def parse_movimentacao_report(year: int, path: Path) -> MovimentacaoReport:
    sheets = read_xlsx(path)
    rows = sheets.get(_SHEET, [])
    return MovimentacaoReport(year=year, rows=_parse_movimentacao(rows))
