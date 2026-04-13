import subprocess
import sys
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"
PYTHON = sys.executable

_FILE_2024 = str(SAMPLES_DIR / "relatorio-consolidado-anual-2024.xlsx")
_FILE_2022 = str(SAMPLES_DIR / "relatorio-consolidado-anual-2022.xlsx")
_MOV_2022 = str(
    Path(__file__).parent.parent.parent / "private-data" / "movimentacao-2022.xlsx"
)


def _run_import(
    year: int, file: str, db: str, movimentacao: str | None = None
) -> subprocess.CompletedProcess[str]:
    cmd = [
        PYTHON,
        "-m",
        "contabilidade",
        "import",
        str(year),
        "--file",
        file,
        "--db",
        db,
    ]
    if movimentacao:
        cmd += ["--movimentacao", movimentacao]
    return subprocess.run(cmd, capture_output=True, text=True)


def _run_report(year: int, db: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "-m", "contabilidade", "report", str(year), "--db", db],
        capture_output=True,
        text=True,
    )


def _run_list(db: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "-m", "contabilidade", "list", "--db", db],
        capture_output=True,
        text=True,
    )


def test_import_exits_zero(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    result = _run_import(2024, _FILE_2024, db)
    assert result.returncode == 0, result.stderr


def test_import_prints_success_message(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    result = _run_import(2024, _FILE_2024, db)
    assert "Importado 2024" in result.stdout


def test_import_then_report_exits_zero(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    _run_import(2024, _FILE_2024, db)
    result = _run_report(2024, db)
    assert result.returncode == 0, result.stderr


def test_import_then_report_contains_required_sections(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    _run_import(2024, _FILE_2024, db)
    result = _run_report(2024, db)
    assert "BENS E DIREITOS" in result.stdout
    assert "RENDIMENTOS ISENTOS" in result.stdout
    assert "TRIBUTAÇÃO EXCLUSIVA" in result.stdout
    assert "RENDA VARIÁVEL" in result.stdout
    assert "RESUMO" in result.stdout


def test_import_then_report_contains_known_tickers(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    _run_import(2024, _FILE_2024, db)
    result = _run_report(2024, db)
    assert "ITSA4" in result.stdout
    assert "VALE3" in result.stdout


def test_reimport_replaces_not_duplicates(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    _run_import(2024, _FILE_2024, db)
    _run_import(2024, _FILE_2024, db)  # Re-import same data
    result = _run_report(2024, db)
    assert result.returncode == 0
    # ITSA4 value should appear — and not be doubled
    assert result.stdout.count("1.270,19") == 1


def test_report_without_file_year_not_in_db_exits_one(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    # Do NOT import anything
    result = _run_report(2023, db)
    assert result.returncode == 1
    assert "não encontrado" in result.stderr or "2023" in result.stderr


def test_list_shows_imported_years(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    _run_import(2024, _FILE_2024, db)
    result = _run_list(db)
    assert result.returncode == 0
    assert "2024" in result.stdout
    assert "b3_report" in result.stdout


def test_import_with_movimentacao_then_report(tmp_path: Path) -> None:
    mov_path = Path(_MOV_2022)
    if not mov_path.exists():
        return  # Skip if private data not available
    db = str(tmp_path / "test.db")
    _run_import(2022, _FILE_2022, db, movimentacao=str(mov_path))
    result = _run_report(2022, db)
    assert result.returncode == 0
    # With movimentacao, reconciliation section should be present
    assert "Reconciliação" in result.stdout or "Operações" in result.stdout
