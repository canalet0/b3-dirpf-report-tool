import subprocess
import sys
from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"
PYTHON = sys.executable


def _run(year: int, filename: str) -> subprocess.CompletedProcess[str]:
    xlsx = SAMPLES_DIR / filename
    return subprocess.run(
        [PYTHON, "-m", "contabilidade", "report", str(year), "--file", str(xlsx)],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "year,filename",
    [
        (2021, "relatorio-consolidado-anual-2021.xlsx"),
        (2022, "relatorio-consolidado-anual-2022.xlsx"),
        (2023, "relatorio-consolidado-anual-2023.xlsx"),
        (2024, "relatorio-consolidado-anual-2024.xlsx"),
        (2025, "relatorio-consolidado-anual-2025.xlsx"),
    ],
)
def test_report_exits_zero(year: int, filename: str) -> None:
    result = _run(year, filename)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "year,filename",
    [
        (2023, "relatorio-consolidado-anual-2023.xlsx"),
        (2024, "relatorio-consolidado-anual-2024.xlsx"),
    ],
)
def test_report_contains_required_sections(year: int, filename: str) -> None:
    result = _run(year, filename)
    assert "BENS E DIREITOS" in result.stdout
    assert "RENDIMENTOS ISENTOS" in result.stdout
    assert "TRIBUTAÇÃO EXCLUSIVA" in result.stdout
    assert "RENDA VARIÁVEL" in result.stdout
    assert "RESUMO" in result.stdout


def test_report_2024_contains_known_tickers() -> None:
    result = _run(2024, "relatorio-consolidado-anual-2024.xlsx")
    assert "ITSA4" in result.stdout
    assert "VALE3" in result.stdout
    assert "HGRE11" in result.stdout


def test_report_2024_contains_correct_acao_value() -> None:
    result = _run(2024, "relatorio-consolidado-anual-2024.xlsx")
    # ITSA4: 143.85 shares * R$ 8.83 = R$ 1270.19
    assert "1.270,19" in result.stdout


def test_report_2024_contains_etf_tickers() -> None:
    result = _run(2024, "relatorio-consolidado-anual-2024.xlsx")
    assert "HASH11" in result.stdout or "IVVB11" in result.stdout


def test_report_2023_contains_more_stocks() -> None:
    result = _run(2023, "relatorio-consolidado-anual-2023.xlsx")
    for ticker in ("GRND3", "ITSA4", "KLBN11", "SLCE3", "TOTS3", "VALE3"):
        assert ticker in result.stdout


def test_report_missing_file_exits_one() -> None:
    result = subprocess.run(
        [PYTHON, "-m", "contabilidade", "report", "2024", "--file", "nonexistent.xlsx"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "não encontrado" in result.stderr or "not found" in result.stderr.lower()


def test_report_invalid_year_exits_one() -> None:
    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "contabilidade",
            "report",
            "2005",
            "--file",
            str(SAMPLES_DIR / "relatorio-consolidado-anual-2024.xlsx"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_report_2020_empty_exits_gracefully() -> None:
    result = _run(2020, "relatorio-consolidado-anual-2020.xlsx")
    # Year 2020 is empty — should either produce empty report or exit with error, not crash
    assert result.returncode in (0, 1)
    assert "Traceback" not in result.stderr
