# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
make install          # create venv and install all dependencies

# Tests
make test-unit        # unit tests with coverage
make test-e2e         # e2e tests against sample xlsx files
make test             # both

# Single test
venv/bin/pytest test/unit/mapper/test_bens_e_direitos.py::test_map_acoes_returns_correct_grupo_codigo

# Linting (all three must pass)
make lint             # black check + pylint + mypy
make black-formatter-fix  # auto-fix formatting

# Run the tool
python -m contabilidade report 2024 --file samples/relatorio-consolidado-anual-2024.xlsx
python -m contabilidade report 2024 --file samples/... --output report.md
```

## Architecture

Three-layer pipeline: **xlsx file → Parser → B3 domain models → Mapper → DIRPF entries → Report → stdout/file**

```
src/contabilidade/
  models/b3.py        # Frozen dataclasses for each B3 sheet row (AcaoPosition, EtfPosition, etc.)
  models/dirpf.py     # Frozen dataclasses for DIRPF output (BenDireito, RendimentoIsentoNaoTributavel, etc.)
  parser/
    xlsx_reader.py    # openpyxl → dict[sheet_name, list[list[str|None]]]; strips empty/total rows
    sheet_parser.py   # raw rows → typed B3Report; all sheets optional (missing → empty list)
  mapper/
    bens_e_direitos.py  # positions → BenDireito entries (Grupo/Código assignment per asset type)
    rendimentos.py      # proventos + reembolsos → income entries (classifies by tipo_evento string)
    renda_variavel.py   # emprestimos → guidance notes (Doador positions get a special note)
  report/
    formatter.py      # DirpfReport → markdown string
    writer.py         # stdout or file
  cli.py              # argparse: `report YEAR --file PATH [--output PATH]`
```

## Key Implementation Details

**Decimal parsing (`_to_decimal`):** xlsx cells come as Python floats converted to strings (e.g. `"143.85"`). The parser distinguishes between dot-decimal (`"143.85"`) and BR-format (`"1.270,19"`) — do not blindly strip `.`. The sentinel `"-"` maps to `Decimal("0")`.

**Renda Fixa values:** Always use `Valor Atualizado CURVA` (column index 16), never MTM (index 14).

**DIRPF mapping table:**

| Source sheet | Grupo | Código | Income section |
|---|---|---|---|
| Posição - Ações | 03 | 01 | — |
| Posição - ETF | 07 | 09 | — |
| Posição - Fundos | 07 | 03 | — |
| Renda Fixa CDB/LCI/LCA | 04 | 02 | — |
| Renda Fixa Debenture | 04 | 03 | — |
| Tesouro Direto | 04 | 04 | — |
| Proventos: Dividendo | — | — | Isentos Linha 09 |
| Proventos: Rendimento (FII) | — | — | Isentos Linha 26 |
| Proventos: Juros s/ Capital Próprio | — | — | Exclusiva Linha 10 |
| Reembolsos de Empréstimo | — | — | Exclusiva Linha 10 |

**`valor_anterior`** is always `Decimal("0")` — the xlsx is a year-end snapshot with no prior-year data; the user fills it from their previous DIRPF.

## Tooling Notes

- `PYTHONPATH = src` (set in Makefile and `.pytest.ini`)
- `mypy.ini` sets `mypy_path = src` and ignores openpyxl stubs
- pylint max line length: 120; docstrings disabled project-wide
- All dataclasses with >7 fields carry `# pylint: disable=too-many-instance-attributes`
- Sample files in `samples/` cover years 2020–2025; 2020 is empty/unparseable
