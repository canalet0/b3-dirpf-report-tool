import argparse
import sys
from datetime import datetime
from pathlib import Path

from contabilidade.mapper.bens_e_direitos import (
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
from contabilidade.models.dirpf import (
    DirpfReport,
    EventoCorporativo,
    ResumoMensalRendaVariavel,
)
from contabilidade.parser.movimentacao_parser import parse_movimentacao_report
from contabilidade.parser.sheet_parser import parse_b3_report
from contabilidade.report.formatter import format_report
from contabilidade.report.writer import write_report


def _build_dirpf_report(
    year: int, xlsx_path: Path, movimentacao_path: Path | None = None
) -> DirpfReport:
    b3 = parse_b3_report(year, xlsx_path)

    bens = (
        map_acoes(b3.acoes, year)
        + map_etfs(b3.etfs, year)
        + map_fundos(b3.fundos, year)
        + map_renda_fixa(b3.renda_fixa, year)
        + map_tesouro_direto(b3.tesouro_direto, year)
    )

    isentos, exclusivos = map_proventos(b3.proventos)
    exclusivos = exclusivos + map_reembolsos(b3.reembolsos)

    notas = map_renda_variavel(b3.emprestimos, year)

    renda_variavel_operacoes: list[ResumoMensalRendaVariavel] = []
    eventos_corporativos: list[EventoCorporativo] = []
    income_reconciliation: list[str] = []

    if movimentacao_path is not None:
        mov_report = parse_movimentacao_report(year, movimentacao_path)
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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="contabilidade",
        description="Gera relatório DIRPF a partir do relatório consolidado anual da B3.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report",
        help="Gera relatório DIRPF para um ano fiscal.",
    )
    report_parser.add_argument(
        "year",
        type=int,
        help="Ano fiscal (ex.: 2024)",
    )
    report_parser.add_argument(
        "--file",
        "-f",
        required=True,
        type=Path,
        metavar="PATH",
        help="Caminho para o arquivo .xlsx da B3.",
    )
    report_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="PATH",
        default=None,
        help="Caminho para salvar o relatório (padrão: stdout).",
    )
    report_parser.add_argument(
        "--movimentacao",
        "-m",
        type=Path,
        metavar="PATH",
        default=None,
        help="Caminho para o arquivo movimentacao-YEAR.xlsx da B3 (opcional).",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    current_year = datetime.now().year
    if args.year < 2021 or args.year > current_year:
        print(
            f"Erro: ano {args.year} fora do intervalo suportado (2021–{current_year}).",
            file=sys.stderr,
        )
        sys.exit(1)

    xlsx_path: Path = args.file
    if not xlsx_path.exists():
        print(f"Erro: arquivo não encontrado: {xlsx_path}", file=sys.stderr)
        sys.exit(1)
    if not xlsx_path.suffix.lower() == ".xlsx":
        print(f"Erro: o arquivo deve ter extensão .xlsx: {xlsx_path}", file=sys.stderr)
        sys.exit(1)

    mov_path: Path | None = args.movimentacao
    if mov_path is not None:
        if not mov_path.exists():
            print(f"Erro: arquivo não encontrado: {mov_path}", file=sys.stderr)
            sys.exit(1)
        if not mov_path.suffix.lower() == ".xlsx":
            print(
                f"Erro: o arquivo deve ter extensão .xlsx: {mov_path}", file=sys.stderr
            )
            sys.exit(1)

    try:
        dirpf = _build_dirpf_report(args.year, xlsx_path, mov_path)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Erro ao processar o arquivo: {exc}", file=sys.stderr)
        sys.exit(1)

    content = format_report(dirpf, xlsx_path)
    write_report(content, args.output)
