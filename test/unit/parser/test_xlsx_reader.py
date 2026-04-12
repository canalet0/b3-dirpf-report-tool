import io
from pathlib import Path

import openpyxl
import pytest

from contabilidade.parser.xlsx_reader import read_xlsx


def _make_xlsx(sheets: dict[str, list[tuple[object, ...]]]) -> Path:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # type: ignore[arg-type]
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    tmp = Path("/tmp/test_xlsx_reader_fixture.xlsx")
    tmp.write_bytes(buf.read())
    return tmp


def test_read_xlsx_returns_all_sheets() -> None:
    path = _make_xlsx({"Sheet1": [("A", "B"), (1, 2)], "Sheet2": [("X",), (3,)]})
    result = read_xlsx(path)
    assert set(result.keys()) == {"Sheet1", "Sheet2"}


def test_read_xlsx_strips_trailing_empty_rows() -> None:
    path = _make_xlsx({"Sheet1": [("A", "B"), (1, 2), (None, None), (None, None)]})
    rows = read_xlsx(path)["Sheet1"]
    assert len(rows) == 2


def test_read_xlsx_strips_total_row() -> None:
    path = _make_xlsx(
        {"Sheet1": [("Produto", "Valor"), ("ITSA4", 100.0), (None, "Total", 100.0)]}
    )
    rows = read_xlsx(path)["Sheet1"]
    # Total row should be stripped
    assert all("Total" not in str(c) for row in rows for c in row if c is not None)


def test_read_xlsx_converts_values_to_str() -> None:
    path = _make_xlsx({"Sheet1": [("A",), (143.85,)]})
    rows = read_xlsx(path)["Sheet1"]
    assert rows[1][0] == "143.85"


def test_read_xlsx_empty_cells_become_none() -> None:
    path = _make_xlsx({"Sheet1": [("A", "B"), (1, None)]})
    rows = read_xlsx(path)["Sheet1"]
    assert rows[1][1] is None


def test_read_xlsx_missing_sheet_not_in_result() -> None:
    path = _make_xlsx({"Sheet1": [("A",)]})
    result = read_xlsx(path)
    assert "NonExistent" not in result


@pytest.mark.parametrize("total_label", ["Total", "total", "TOTAL"])
def test_read_xlsx_strips_total_regardless_of_case(total_label: str) -> None:
    path = _make_xlsx({"Sheet1": [("A", "B"), (1, 2), (None, total_label)]})
    rows = read_xlsx(path)["Sheet1"]
    last_row_values = [c for c in rows[-1] if c is not None]
    assert total_label not in last_row_values
