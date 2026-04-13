from decimal import Decimal

from contabilidade.models.dirpf import (
    BenDireito,
    DirpfReport,
    RendaVariavelNota,
    RendimentoIsentoNaoTributavel,
    RendimentoTributacaoExclusiva,
)
from contabilidade.report.formatter import _brl, format_report

_SAMPLE_LABEL = "samples/test.xlsx"


def test_brl_formats_br_locale() -> None:
    assert _brl(Decimal("1270.19")) == "R$ 1.270,19"


def test_brl_zero() -> None:
    assert _brl(Decimal("0")) == "R$ 0,00"


def test_brl_large_value() -> None:
    assert _brl(Decimal("1234567.89")) == "R$ 1.234.567,89"


def _make_report() -> DirpfReport:
    return DirpfReport(
        year=2024,
        bens_e_direitos=[
            BenDireito(
                grupo="03",
                codigo="01",
                cnpj="61.532.644/0001-15",
                discriminacao="QUANTIDADE: 143 ações de ITAUSA S.A. (ITSA4 PN)",
                valor_anterior=Decimal("0"),
                valor_atual=Decimal("1270.19"),
            )
        ],
        rendimentos_isentos=[
            RendimentoIsentoNaoTributavel(
                linha="09",
                tipo="Lucros e dividendos recebidos",
                beneficiario="ITSA4",
                valor=Decimal("41.16"),
                observacao="Instrução de preenchimento.",
            )
        ],
        rendimentos_exclusivos=[
            RendimentoTributacaoExclusiva(
                linha="10",
                tipo="Juros sobre Capital Próprio",
                beneficiario="VALE3",
                cnpj_fonte="",
                valor=Decimal("19.50"),
                observacao="Instrução JCP.",
            )
        ],
        renda_variavel_notas=[
            RendaVariavelNota(mensagem="Atenção: use extrato mensal.")
        ],
    )


def test_format_report_contains_year_header() -> None:
    content = format_report(_make_report(), _SAMPLE_LABEL)
    assert "2024" in content


def test_format_report_contains_bens_e_direitos_section() -> None:
    content = format_report(_make_report(), _SAMPLE_LABEL)
    assert "BENS E DIREITOS" in content


def test_format_report_contains_rendimentos_isentos_section() -> None:
    content = format_report(_make_report(), _SAMPLE_LABEL)
    assert "RENDIMENTOS ISENTOS" in content


def test_format_report_contains_rendimentos_exclusivos_section() -> None:
    content = format_report(_make_report(), _SAMPLE_LABEL)
    assert "TRIBUTAÇÃO EXCLUSIVA" in content


def test_format_report_brl_values_formatted_correctly() -> None:
    content = format_report(_make_report(), _SAMPLE_LABEL)
    assert "R$ 1.270,19" in content


def test_format_report_dividendo_value_appears() -> None:
    content = format_report(_make_report(), _SAMPLE_LABEL)
    assert "R$ 41,16" in content


def test_format_report_contains_resumo() -> None:
    content = format_report(_make_report(), _SAMPLE_LABEL)
    assert "RESUMO" in content


def test_format_report_empty_bens_e_direitos() -> None:
    report = DirpfReport(
        year=2024,
        bens_e_direitos=[],
        rendimentos_isentos=[],
        rendimentos_exclusivos=[],
        renda_variavel_notas=[],
    )
    content = format_report(report, _SAMPLE_LABEL)
    assert "Nenhuma posição encontrada" in content


def test_format_bens_anterior_zero_shows_preencher_note() -> None:
    report = DirpfReport(
        year=2024,
        bens_e_direitos=[
            BenDireito(
                grupo="03",
                codigo="01",
                cnpj="61.532.644/0001-15",
                discriminacao="ITSA4 Situação em 31/12/2023: R$ 0,00",
                valor_anterior=Decimal("0"),
                valor_atual=Decimal("1270.19"),
            )
        ],
        rendimentos_isentos=[],
        rendimentos_exclusivos=[],
        renda_variavel_notas=[],
    )
    content = format_report(report, _SAMPLE_LABEL)
    assert "preencher" in content.lower()


def test_format_bens_anterior_filled_no_preencher_note() -> None:
    report = DirpfReport(
        year=2024,
        bens_e_direitos=[
            BenDireito(
                grupo="03",
                codigo="01",
                cnpj="61.532.644/0001-15",
                discriminacao="ITSA4 Situação em 31/12/2023: R$ 1.100,00",
                valor_anterior=Decimal("1100.00"),
                valor_atual=Decimal("1270.19"),
            )
        ],
        rendimentos_isentos=[],
        rendimentos_exclusivos=[],
        renda_variavel_notas=[],
    )
    content = format_report(report, _SAMPLE_LABEL)
    assert "R$ 1.100,00" in content
    # The "preencher" note should NOT appear for the situacao anterior line
    # (it only appears when valor_anterior == 0)
    lines = [ln for ln in content.splitlines() if "Situação em 31/12/2023" in ln]
    assert lines, "Expected a situacao anterior line"
    assert "preencher" not in lines[0].lower()
