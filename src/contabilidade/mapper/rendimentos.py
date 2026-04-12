from decimal import Decimal

from contabilidade.models.b3 import Provento, Reembolso
from contabilidade.models.dirpf import (
    RendimentoIsentoNaoTributavel,
    RendimentoTributacaoExclusiva,
)

_TIPO_DIVIDENDO = "dividendo"
_TIPO_JCP = "juros sobre capital"
_TIPO_RENDIMENTO_FII = "rendimento"


def _classify_provento(tipo_evento: str) -> str:
    lower = tipo_evento.lower()
    if _TIPO_DIVIDENDO in lower:
        return "dividendo"
    if _TIPO_JCP in lower:
        return "jcp"
    if _TIPO_RENDIMENTO_FII in lower:
        return "rendimento_fii"
    return "outros"


def map_proventos(
    proventos: list[Provento],
) -> tuple[list[RendimentoIsentoNaoTributavel], list[RendimentoTributacaoExclusiva]]:
    isentos: list[RendimentoIsentoNaoTributavel] = []
    exclusivos: list[RendimentoTributacaoExclusiva] = []

    # Accumulate dividends per ticker
    dividendos: dict[str, Decimal] = {}
    rendimentos_fii: dict[str, Decimal] = {}
    jcp: dict[str, Decimal] = {}
    outros: dict[str, Decimal] = {}

    for prov in proventos:
        kind = _classify_provento(prov.tipo_evento)
        if kind == "dividendo":
            dividendos[prov.produto] = (
                dividendos.get(prov.produto, Decimal("0")) + prov.valor_liquido
            )
        elif kind == "jcp":
            jcp[prov.produto] = jcp.get(prov.produto, Decimal("0")) + prov.valor_liquido
        elif kind == "rendimento_fii":
            rendimentos_fii[prov.produto] = (
                rendimentos_fii.get(prov.produto, Decimal("0")) + prov.valor_liquido
            )
        else:
            outros[prov.produto] = (
                outros.get(prov.produto, Decimal("0")) + prov.valor_liquido
            )

    for ticker, valor in dividendos.items():
        isentos.append(
            RendimentoIsentoNaoTributavel(
                linha="09",
                tipo="Lucros e dividendos recebidos",
                beneficiario=ticker,
                valor=valor,
                observacao=(
                    "Rendimentos Isentos > Linha 09 — Lucros e dividendos recebidos. "
                    "Informar o CNPJ da empresa pagadora e o valor recebido líquido."
                ),
            )
        )

    for ticker, valor in rendimentos_fii.items():
        isentos.append(
            RendimentoIsentoNaoTributavel(
                linha="26",
                tipo="Rendimentos de Fundos de Investimento Imobiliário (FII)",
                beneficiario=ticker,
                valor=valor,
                observacao=(
                    "Rendimentos Isentos > Linha 26 — Rendimentos de FII. "
                    "Isentos de IR para pessoa física conforme Lei 9.779/99, "
                    "desde que o fundo seja negociado em bolsa com no mínimo 50 cotistas."
                ),
            )
        )

    for ticker, valor in outros.items():
        isentos.append(
            RendimentoIsentoNaoTributavel(
                linha="99",
                tipo=f"Outros rendimentos — {ticker}",
                beneficiario=ticker,
                valor=valor,
                observacao=(
                    "Verificar a natureza do rendimento com o informe de rendimentos "
                    "da corretora para determinar a linha correta na DIRPF."
                ),
            )
        )

    for ticker, valor in jcp.items():
        exclusivos.append(
            RendimentoTributacaoExclusiva(
                linha="10",
                tipo="Juros sobre Capital Próprio",
                beneficiario=ticker,
                cnpj_fonte="",
                valor=valor,
                observacao=(
                    "Rendimentos Sujeitos à Tributação Exclusiva > Linha 10 — "
                    "Juros sobre capital próprio. "
                    "O IR (15%) já foi retido na fonte pela empresa pagadora. "
                    "Consulte o informe de rendimentos da corretora para o CNPJ da fonte pagadora."
                ),
            )
        )

    return isentos, exclusivos


def map_reembolsos(
    reembolsos: list[Reembolso],
) -> list[RendimentoTributacaoExclusiva]:
    result: list[RendimentoTributacaoExclusiva] = []
    accumulated: dict[str, Decimal] = {}
    for r in reembolsos:
        accumulated[r.produto] = (
            accumulated.get(r.produto, Decimal("0")) + r.valor_liquido
        )

    for ticker, valor in accumulated.items():
        result.append(
            RendimentoTributacaoExclusiva(
                linha="10",
                tipo="Reembolso de Empréstimo (BTC — Aluguel de Ações)",
                beneficiario=ticker,
                cnpj_fonte="",
                valor=valor,
                observacao=(
                    "Reembolsos recebidos do programa de aluguel de ações (BTC) da B3. "
                    "Tributação exclusiva. Consulte seu contador para a linha exata "
                    "e o CNPJ da fonte pagadora no informe de rendimentos da corretora."
                ),
            )
        )
    return result
