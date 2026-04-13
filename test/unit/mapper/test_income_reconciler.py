from decimal import Decimal

from contabilidade.mapper.income_reconciler import reconcile_income
from contabilidade.models.b3 import Provento, Reembolso


def _prov(tipo: str, valor: str) -> Provento:
    return Provento(produto="ITSA4", tipo_evento=tipo, valor_liquido=Decimal(valor))


def _reimb(valor: str) -> Reembolso:
    return Reembolso(
        produto="TAEE11", tipo_evento="Reembolso", valor_liquido=Decimal(valor)
    )


def test_empty_inputs_returns_empty() -> None:
    assert not reconcile_income([], [], {})


def test_match_produces_checkmark() -> None:
    proventos = [_prov("Dividendo", "41.16")]
    mov = {"dividendo": Decimal("41.16")}
    messages = reconcile_income(proventos, [], mov)
    assert any("✓" in m and "Dividendos" in m for m in messages)


def test_mismatch_produces_warning() -> None:
    proventos = [_prov("Juros Sobre Capital Próprio", "95.44")]
    mov = {"jcp": Decimal("94.02")}
    messages = reconcile_income(proventos, [], mov)
    assert any("⚠" in m and "JCP" in m for m in messages)


def test_mismatch_shows_difference() -> None:
    proventos = [_prov("Juros Sobre Capital Próprio", "95.44")]
    mov = {"jcp": Decimal("94.02")}
    messages = reconcile_income(proventos, [], mov)
    jcp_msg = next(m for m in messages if "JCP" in m)
    assert "1,42" in jcp_msg


def test_reembolsos_included() -> None:
    reimbs = [_reimb("30.00")]
    mov = {"reembolso": Decimal("30.00")}
    messages = reconcile_income([], reimbs, mov)
    assert any("Reembolsos" in m for m in messages)


def test_missing_in_movimentacao_shows_mismatch() -> None:
    proventos = [_prov("Dividendo", "41.16")]
    messages = reconcile_income(proventos, [], {})
    assert any("⚠" in m or "✓" in m for m in messages)


def test_missing_in_proventos_shows_mismatch() -> None:
    mov = {"dividendo": Decimal("41.16")}
    messages = reconcile_income([], [], mov)
    assert any("⚠" in m for m in messages)
