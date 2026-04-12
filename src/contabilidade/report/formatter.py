from datetime import datetime
from decimal import Decimal
from pathlib import Path

from contabilidade.models.dirpf import (
    BenDireito,
    DirpfReport,
    RendaVariavelNota,
    RendimentoIsentoNaoTributavel,
    RendimentoTributacaoExclusiva,
)


def _brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}"
    # Convert US format (1,234.56) to BR format (1.234,56)
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _section(title: str) -> str:
    return f"\n## {title}\n"


def _subsection(title: str) -> str:
    return f"\n### {title}\n"


def _format_bens_e_direitos(bens: list[BenDireito], year: int) -> str:
    if not bens:
        return "\n*Nenhuma posição encontrada.*\n"

    # Group by (grupo, codigo)
    groups: dict[tuple[str, str], list[BenDireito]] = {}
    for b in bens:
        key = (b.grupo, b.codigo)
        groups.setdefault(key, []).append(b)

    group_labels: dict[tuple[str, str], str] = {
        ("03", "01"): "Grupo 03, Código 01 — Ações",
        (
            "04",
            "02",
        ): "Grupo 04, Código 02 — Títulos de Renda Fixa (CDB, LCI, LCA, LIG)",
        ("04", "03"): "Grupo 04, Código 03 — Debêntures",
        ("04", "04"): "Grupo 04, Código 04 — Tesouro Direto",
        ("07", "03"): "Grupo 07, Código 03 — Fundos de Investimento (incluindo FII)",
        ("07", "09"): "Grupo 07, Código 09 — ETFs (Fundos de Índice)",
    }

    lines: list[str] = []
    total_atual = Decimal("0")

    sorted_keys = sorted(groups.keys())
    for key in sorted_keys:
        label = group_labels.get(key, f"Grupo {key[0]}, Código {key[1]}")
        lines.append(_subsection(label))
        lines.append(
            f"> Em Bens e Direitos, adicione um item para cada entrada abaixo "
            f"selecionando Grupo {key[0]} > Código {key[1]}.\n"
        )
        for b in groups[key]:
            lines.append("---")
            if b.cnpj:
                lines.append(f"**CNPJ:** {b.cnpj}  ")
            lines.append("**Discriminação:**")
            lines.append(f"> {b.discriminacao}")
            lines.append("")
            lines.append(
                f"- Situação em 31/12/{year - 1}: {_brl(b.valor_anterior)}  *(preencher com valor da DIRPF anterior)*"
            )
            lines.append(f"- Situação em 31/12/{year}: **{_brl(b.valor_atual)}**")
            lines.append("")
            total_atual += b.valor_atual

    return "\n".join(lines)


def _format_rendimentos_isentos(
    rendimentos: list[RendimentoIsentoNaoTributavel],
) -> str:
    if not rendimentos:
        return "\n*Nenhum rendimento isento encontrado.*\n"

    # Group by linha
    by_linha: dict[str, list[RendimentoIsentoNaoTributavel]] = {}
    for r in rendimentos:
        by_linha.setdefault(r.linha, []).append(r)

    linha_labels: dict[str, str] = {
        "09": "Linha 09 — Lucros e dividendos recebidos",
        "26": "Linha 26 — Rendimentos de Fundos de Investimento Imobiliário (FII)",
        "99": "Outros rendimentos isentos",
    }

    lines: list[str] = []
    for linha in sorted(by_linha.keys()):
        label = linha_labels.get(linha, f"Linha {linha}")
        lines.append(_subsection(label))
        items = by_linha[linha]
        total = Decimal("0")
        lines.append("| Produto | Valor Líquido |")
        lines.append("|---------|---------------|")
        for r in items:
            lines.append(f"| {r.beneficiario} | {_brl(r.valor)} |")
            total += r.valor
        lines.append(f"| **TOTAL** | **{_brl(total)}** |")
        if items:
            lines.append(f"\n> {items[0].observacao}\n")

    return "\n".join(lines)


def _format_rendimentos_exclusivos(
    rendimentos: list[RendimentoTributacaoExclusiva],
) -> str:
    if not rendimentos:
        return "\n*Nenhum rendimento sujeito à tributação exclusiva encontrado.*\n"

    by_tipo: dict[str, list[RendimentoTributacaoExclusiva]] = {}
    for r in rendimentos:
        by_tipo.setdefault(r.tipo, []).append(r)

    lines: list[str] = []
    for tipo in sorted(by_tipo.keys()):
        items = by_tipo[tipo]
        lines.append(_subsection(f"Linha {items[0].linha} — {tipo}"))
        total = Decimal("0")
        lines.append("| Produto | Valor Líquido |")
        lines.append("|---------|---------------|")
        for r in items:
            lines.append(f"| {r.beneficiario} | {_brl(r.valor)} |")
            total += r.valor
        lines.append(f"| **TOTAL** | **{_brl(total)}** |")
        if items:
            lines.append(f"\n> {items[0].observacao}\n")

    return "\n".join(lines)


def _format_renda_variavel(notas: list[RendaVariavelNota]) -> str:
    lines: list[str] = []
    for nota in notas:
        lines.append("")
        for line in nota.mensagem.split("\n"):
            if line.startswith("  - "):
                lines.append(line)
            elif line.startswith("  "):
                lines.append(f"> {line.strip()}")
            elif line:
                lines.append(f"> {line}")
            else:
                lines.append(">")
        lines.append("")
    return "\n".join(lines)


def _format_resumo(report: DirpfReport) -> str:
    lines: list[str] = []
    lines.append("| Seção | Total em 31/12 |")
    lines.append("|-------|----------------|")

    grupo_label: dict[tuple[str, str], str] = {
        ("03", "01"): "Bens e Direitos — Ações",
        ("04", "02"): "Bens e Direitos — Renda Fixa",
        ("04", "03"): "Bens e Direitos — Debêntures",
        ("04", "04"): "Bens e Direitos — Tesouro Direto",
        ("07", "03"): "Bens e Direitos — Fundos / FII",
        ("07", "09"): "Bens e Direitos — ETFs",
    }

    totals: dict[tuple[str, str], Decimal] = {}
    for b in report.bens_e_direitos:
        key = (b.grupo, b.codigo)
        totals[key] = totals.get(key, Decimal("0")) + b.valor_atual

    for key in sorted(totals.keys()):
        label = grupo_label.get(key, f"Grupo {key[0]} Cód {key[1]}")
        lines.append(f"| {label} | {_brl(totals[key])} |")

    total_isentos = sum(r.valor for r in report.rendimentos_isentos)
    if total_isentos:
        lines.append(f"| Rendimentos Isentos (total) | {_brl(total_isentos)} |")

    total_exclusivos = sum(r.valor for r in report.rendimentos_exclusivos)
    if total_exclusivos:
        lines.append(f"| Rendimentos Exclusivos (total) | {_brl(total_exclusivos)} |")

    return "\n".join(lines)


def format_report(report: DirpfReport, source_path: Path) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines: list[str] = []

    lines.append(f"# Relatório DIRPF {report.year} — gerado por contabilidade")
    lines.append("")
    lines.append(f"**Arquivo:** `{source_path}`  ")
    lines.append(f"**Data de geração:** {now}")
    lines.append("")
    lines.append(
        "> **IMPORTANTE:** Este relatório é uma guia baseada nos dados da B3. "
        "Verifique todos os valores com seu contador antes de enviar a DIRPF. "
        "Os valores de **Situação em 31/12 do ano anterior** devem ser preenchidos "
        "com os valores declarados na DIRPF do ano anterior."
    )

    lines.append(_section("BENS E DIREITOS"))
    lines.append(_format_bens_e_direitos(report.bens_e_direitos, report.year))

    lines.append(_section("RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS"))
    lines.append(_format_rendimentos_isentos(report.rendimentos_isentos))

    lines.append(_section("RENDIMENTOS SUJEITOS À TRIBUTAÇÃO EXCLUSIVA/DEFINITIVA"))
    lines.append(_format_rendimentos_exclusivos(report.rendimentos_exclusivos))

    lines.append(_section("RENDA VARIÁVEL"))
    lines.append(_format_renda_variavel(report.renda_variavel_notas))

    lines.append(_section("RESUMO DE VALORES"))
    lines.append(_format_resumo(report))
    lines.append("")

    return "\n".join(lines)
