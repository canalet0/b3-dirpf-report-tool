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
from contabilidade.mapper.renda_variavel import map_renda_variavel
from contabilidade.mapper.rendimentos import map_proventos, map_reembolsos
from contabilidade.models.dirpf import DirpfReport
from contabilidade.parser.sheet_parser import parse_b3_report
from contabilidade.report.formatter import format_report
from contabilidade.report.writer import write_report


def _build_dirpf_report(year: int, xlsx_path: Path) -> DirpfReport:
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

    return DirpfReport(
        year=year,
        bens_e_direitos=bens,
        rendimentos_isentos=isentos,
        rendimentos_exclusivos=exclusivos,
        renda_variavel_notas=notas,
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

    try:
        dirpf = _build_dirpf_report(args.year, xlsx_path)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Erro ao processar o arquivo: {exc}", file=sys.stderr)
        sys.exit(1)

    content = format_report(dirpf, xlsx_path)
    write_report(content, args.output)
