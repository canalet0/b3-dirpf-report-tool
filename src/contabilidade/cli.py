import argparse
import sys
from datetime import datetime
from pathlib import Path

from contabilidade.db.b3_repository import load_b3_report, save_b3_report
from contabilidade.db.connection import default_db_path, open_connection
from contabilidade.db.import_log import (
    has_b3_report,
    has_movimentacao,
    list_imports,
)
from contabilidade.db.movimentacao_repository import (
    load_movimentacao_report,
    save_movimentacao_report,
)
from contabilidade.db.schema import ensure_schema
from contabilidade.mapper.bens_e_direitos import (
    _build_acoes_lookup,
    _build_etfs_lookup,
    _build_fundos_lookup,
    _build_renda_fixa_lookup,
    _build_tesouro_lookup,
    map_acoes,
    map_etfs,
    map_fundos,
    map_renda_fixa,
    map_tesouro_direto,
)
from contabilidade.mapper.income_reconciler import reconcile_income
from contabilidade.mapper.renda_variavel import map_renda_variavel
from contabilidade.mapper.renda_variavel_calc import (
    compute_renda_variavel,
    extract_income_from_movimentacao,
)
from contabilidade.mapper.rendimentos import map_proventos, map_reembolsos
from contabilidade.models.b3 import B3Report
from contabilidade.models.dirpf import (
    DirpfReport,
    EventoCorporativo,
    ResumoMensalRendaVariavel,
)
from contabilidade.models.movimentacao import MovimentacaoReport
from contabilidade.parser.movimentacao_parser import parse_movimentacao_report
from contabilidade.parser.sheet_parser import parse_b3_report
from contabilidade.analyzer.analytics import build_analytics_report
from contabilidade.analyzer.growth import build_growth_report
from contabilidade.report.analytics_formatter import format_analytics_report
from contabilidade.report.formatter import format_report
from contabilidade.report.growth_formatter import format_growth_report
from contabilidade.report.writer import write_report


def _build_dirpf_report(
    b3: B3Report,
    mov_report: MovimentacaoReport | None = None,
    prior_year_b3: B3Report | None = None,
) -> DirpfReport:
    year = b3.year
    bens = (
        map_acoes(
            b3.acoes,
            year,
            _build_acoes_lookup(prior_year_b3.acoes) if prior_year_b3 else None,
        )
        + map_etfs(
            b3.etfs,
            year,
            _build_etfs_lookup(prior_year_b3.etfs) if prior_year_b3 else None,
        )
        + map_fundos(
            b3.fundos,
            year,
            _build_fundos_lookup(prior_year_b3.fundos) if prior_year_b3 else None,
        )
        + map_renda_fixa(
            b3.renda_fixa,
            year,
            (
                _build_renda_fixa_lookup(prior_year_b3.renda_fixa)
                if prior_year_b3
                else None
            ),
        )
        + map_tesouro_direto(
            b3.tesouro_direto,
            year,
            (
                _build_tesouro_lookup(prior_year_b3.tesouro_direto)
                if prior_year_b3
                else None
            ),
        )
    )

    isentos, exclusivos = map_proventos(b3.proventos)
    exclusivos = exclusivos + map_reembolsos(b3.reembolsos)

    notas = map_renda_variavel(b3.emprestimos, year)

    renda_variavel_operacoes: list[ResumoMensalRendaVariavel] = []
    eventos_corporativos: list[EventoCorporativo] = []
    income_reconciliation: list[str] = []

    if mov_report is not None:
        renda_variavel_operacoes, eventos_corporativos = compute_renda_variavel(
            mov_report.rows
        )
        mov_income = extract_income_from_movimentacao(mov_report.rows)
        income_reconciliation = reconcile_income(
            b3.proventos, b3.reembolsos, mov_income
        )

    return DirpfReport(
        year=year,
        bens_e_direitos=bens,
        rendimentos_isentos=isentos,
        rendimentos_exclusivos=exclusivos,
        renda_variavel_notas=notas,
        renda_variavel_operacoes=renda_variavel_operacoes,
        eventos_corporativos=eventos_corporativos,
        income_reconciliation=income_reconciliation,
    )


def _validate_xlsx(path: Path, label: str = "arquivo") -> None:
    if not path.exists():
        print(f"Erro: {label} não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    if path.suffix.lower() != ".xlsx":
        print(f"Erro: o {label} deve ter extensão .xlsx: {path}", file=sys.stderr)
        sys.exit(1)


def _validate_year(year: int) -> None:
    current_year = datetime.now().year
    if year < 2021 or year > current_year:
        print(
            f"Erro: ano {year} fora do intervalo suportado (2021–{current_year}).",
            file=sys.stderr,
        )
        sys.exit(1)


def _handle_import(args: argparse.Namespace) -> None:
    year: int = args.year
    _validate_year(year)

    xlsx_path: Path = args.file
    _validate_xlsx(xlsx_path, "arquivo")

    mov_path: Path | None = args.movimentacao
    if mov_path is not None:
        _validate_xlsx(mov_path, "arquivo de movimentação")

    try:
        b3 = parse_b3_report(year, xlsx_path)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Erro ao processar o arquivo: {exc}", file=sys.stderr)
        sys.exit(1)

    db_path: Path = args.db if args.db is not None else default_db_path()
    conn = open_connection(db_path)
    ensure_schema(conn)
    save_b3_report(conn, b3)
    print(f"Importado {year} (b3_report) com sucesso.")

    if mov_path is not None:
        try:
            mov_report = parse_movimentacao_report(year, mov_path)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            print(
                f"Erro ao processar o arquivo de movimentação: {exc}", file=sys.stderr
            )
            sys.exit(1)
        save_movimentacao_report(conn, mov_report)
        print(f"Importado {year} (movimentacao) com sucesso.")

    conn.close()


def _load_prior_year(db_path: Path, year: int) -> B3Report | None:
    """Load the prior year B3 report from db if available; returns None on any failure."""
    if not db_path.exists():
        return None
    try:
        conn = open_connection(db_path)
        ensure_schema(conn)
        prior: B3Report | None = None
        if has_b3_report(conn, year - 1):
            prior = load_b3_report(conn, year - 1)
        conn.close()
        return prior
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def _handle_report(  # pylint: disable=too-many-branches,too-many-locals
    args: argparse.Namespace,
) -> None:
    year: int = args.year
    _validate_year(year)

    xlsx_path: Path | None = args.file
    mov_path: Path | None = getattr(args, "movimentacao", None)

    if xlsx_path is not None:
        # Direct xlsx path — unchanged behaviour, no db interaction
        _validate_xlsx(xlsx_path, "arquivo")
        if mov_path is not None:
            _validate_xlsx(mov_path, "arquivo de movimentação")

        try:
            b3 = parse_b3_report(year, xlsx_path)
            mov_report: MovimentacaoReport | None = None
            if mov_path is not None:
                mov_report = parse_movimentacao_report(year, mov_path)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            print(f"Erro ao processar o arquivo: {exc}", file=sys.stderr)
            sys.exit(1)

        db_path_prior: Path = args.db if args.db is not None else default_db_path()
        prior_b3_file = _load_prior_year(db_path_prior, year)
        dirpf = _build_dirpf_report(b3, mov_report, prior_b3_file)
        source_label = str(xlsx_path)
    else:
        # Load from db
        db_path: Path = args.db if args.db is not None else default_db_path()
        conn = open_connection(db_path)
        ensure_schema(conn)

        if not has_b3_report(conn, year):
            print(
                f"Erro: dados para o ano {year} não encontrados no banco. "
                f"Use 'import {year} --file PATH' para importar.",
                file=sys.stderr,
            )
            conn.close()
            sys.exit(1)

        b3_loaded = load_b3_report(conn, year)
        if b3_loaded is None:
            print(
                f"Erro: falha ao carregar dados do banco para {year}.", file=sys.stderr
            )
            conn.close()
            sys.exit(1)

        mov_loaded: MovimentacaoReport | None = None
        if has_movimentacao(conn, year):
            mov_loaded = load_movimentacao_report(conn, year)

        prior_b3 = (
            load_b3_report(conn, year - 1) if has_b3_report(conn, year - 1) else None
        )
        conn.close()
        dirpf = _build_dirpf_report(b3_loaded, mov_loaded, prior_b3)
        source_label = f"db:{db_path}:{year}"

    content = format_report(dirpf, source_label)
    write_report(content, args.output)


def _handle_growth(args: argparse.Namespace) -> None:
    db_path: Path = args.db if args.db is not None else default_db_path()
    conn = open_connection(db_path)
    ensure_schema(conn)

    entries = list_imports(conn)
    b3_years = sorted({e.year for e in entries if e.source_type == "b3_report"})

    if not b3_years:
        print(
            "Erro: nenhum dado importado. Use 'import YEAR --file PATH' para importar.",
            file=sys.stderr,
        )
        conn.close()
        sys.exit(1)

    report = build_growth_report(conn, b3_years)
    conn.close()

    content = format_growth_report(report, str(db_path))
    write_report(content, args.output)


def _handle_analytics(args: argparse.Namespace) -> None:
    db_path: Path = args.db if args.db is not None else default_db_path()
    conn = open_connection(db_path)
    ensure_schema(conn)

    entries = list_imports(conn)
    b3_years = sorted({e.year for e in entries if e.source_type == "b3_report"})

    if not b3_years:
        print(
            "Erro: nenhum dado importado. Use 'import YEAR --file PATH' para importar.",
            file=sys.stderr,
        )
        conn.close()
        sys.exit(1)

    report = build_analytics_report(conn, b3_years)
    conn.close()

    content = format_analytics_report(report, str(db_path))
    write_report(content, args.output)


def _handle_list(args: argparse.Namespace) -> None:
    db_path: Path = args.db if args.db is not None else default_db_path()
    conn = open_connection(db_path)
    ensure_schema(conn)
    entries = list_imports(conn)
    conn.close()

    if not entries:
        print(f"Nenhum dado importado em {db_path}.")
        return

    print(f"Dados disponíveis no banco ({db_path}):")
    for e in entries:
        print(f"  {e.year}  {e.source_type:<15}  importado em {e.imported_at}")


def _add_db_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--db",
        type=Path,
        metavar="PATH",
        default=None,
        help=f"Caminho para o banco de dados SQLite (padrão: {default_db_path()}).",
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="contabilidade",
        description="Gera relatório DIRPF a partir do relatório consolidado anual da B3.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- report ---
    report_parser = subparsers.add_parser(
        "report",
        help="Gera relatório DIRPF para um ano fiscal.",
    )
    report_parser.add_argument("year", type=int, help="Ano fiscal (ex.: 2024)")
    report_parser.add_argument(
        "--file",
        "-f",
        required=False,
        default=None,
        type=Path,
        metavar="PATH",
        help="Caminho para o arquivo .xlsx da B3 (opcional se dados já importados).",
    )
    report_parser.add_argument(
        "--movimentacao",
        "-m",
        type=Path,
        metavar="PATH",
        default=None,
        help="Caminho para o arquivo movimentacao-YEAR.xlsx da B3 (opcional).",
    )
    report_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="PATH",
        default=None,
        help="Caminho para salvar o relatório (padrão: stdout).",
    )
    _add_db_arg(report_parser)

    # --- import ---
    import_parser = subparsers.add_parser(
        "import",
        help="Importa dados do xlsx para o banco de dados.",
    )
    import_parser.add_argument("year", type=int, help="Ano fiscal (ex.: 2024)")
    import_parser.add_argument(
        "--file",
        "-f",
        required=True,
        type=Path,
        metavar="PATH",
        help="Caminho para o arquivo .xlsx da B3.",
    )
    import_parser.add_argument(
        "--movimentacao",
        "-m",
        type=Path,
        metavar="PATH",
        default=None,
        help="Caminho para o arquivo movimentacao-YEAR.xlsx da B3 (opcional).",
    )
    _add_db_arg(import_parser)

    # --- growth ---
    growth_parser = subparsers.add_parser(
        "growth",
        help="Gera relatório de crescimento da carteira ao longo dos anos importados.",
    )
    growth_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="PATH",
        default=None,
        help="Caminho para salvar o relatório (padrão: stdout).",
    )
    _add_db_arg(growth_parser)

    # --- analytics ---
    analytics_parser = subparsers.add_parser(
        "analytics",
        help="Gera relatório de analytics da carteira (desempenho, yield, custo médio).",
    )
    analytics_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="PATH",
        default=None,
        help="Caminho para salvar o relatório (padrão: stdout).",
    )
    _add_db_arg(analytics_parser)

    # --- list ---
    list_parser = subparsers.add_parser(
        "list",
        help="Lista os anos importados no banco de dados.",
    )
    _add_db_arg(list_parser)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.command == "import":
        _handle_import(args)
    elif args.command == "report":
        _handle_report(args)
    elif args.command == "growth":
        _handle_growth(args)
    elif args.command == "analytics":
        _handle_analytics(args)
    elif args.command == "list":
        _handle_list(args)
