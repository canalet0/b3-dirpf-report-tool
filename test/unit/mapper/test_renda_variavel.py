from decimal import Decimal

from contabilidade.mapper.renda_variavel import map_renda_variavel
from contabilidade.models.b3 import EmprestimoPosition


def _emp(produto: str, natureza: str, qtd: str = "34") -> EmprestimoPosition:
    return EmprestimoPosition(
        produto=produto,
        instituicao="INTER",
        natureza=natureza,
        numero_contrato="CONT001",
        taxa=Decimal("0.32"),
        data_registro="01/01/2024",
        data_vencimento="04/02/2025",
        quantidade=Decimal(qtd),
        valor_atualizado=Decimal("459.0"),
    )


def test_always_includes_general_guidance_note() -> None:
    notas = map_renda_variavel([], 2024)
    assert len(notas) >= 1
    assert (
        "extrato" in notas[0].mensagem.lower()
        or "histórico" in notas[0].mensagem.lower()
    )


def test_doador_positions_produce_additional_note() -> None:
    notas = map_renda_variavel([_emp("TAEE11 - TAESA", "Doador")], 2024)
    assert len(notas) == 2
    assert "TAEE11" in notas[1].mensagem


def test_tomador_positions_do_not_produce_extra_note() -> None:
    notas = map_renda_variavel([_emp("TAEE11 - TAESA", "Tomador")], 2024)
    assert len(notas) == 1


def test_doador_note_includes_year() -> None:
    notas = map_renda_variavel([_emp("TAEE11 - TAESA", "Doador")], 2024)
    assert "2024" in notas[1].mensagem


def test_empty_emprestimos_returns_one_general_note() -> None:
    notas = map_renda_variavel([], 2023)
    assert len(notas) == 1
