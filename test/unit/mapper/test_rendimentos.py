from decimal import Decimal

from contabilidade.mapper.rendimentos import map_proventos, map_reembolsos
from contabilidade.models.b3 import Provento, Reembolso


def _prov(produto: str, tipo: str, valor: str) -> Provento:
    return Provento(produto=produto, tipo_evento=tipo, valor_liquido=Decimal(valor))


def _reimb(produto: str, valor: str) -> Reembolso:
    return Reembolso(
        produto=produto, tipo_evento="Reembolso", valor_liquido=Decimal(valor)
    )


def test_dividendo_goes_to_isentos_linha_09() -> None:
    isentos, exclusivos = map_proventos([_prov("ITSA4", "Dividendo", "41.16")])
    assert len(exclusivos) == 0
    assert len(isentos) == 1
    assert isentos[0].linha == "09"
    assert isentos[0].beneficiario == "ITSA4"
    assert isentos[0].valor == Decimal("41.16")


def test_jcp_goes_to_exclusivos_linha_10() -> None:
    isentos, exclusivos = map_proventos(
        [_prov("VALE3", "Juros Sobre Capital Próprio", "19.50")]
    )
    assert len(isentos) == 0
    assert len(exclusivos) == 1
    assert exclusivos[0].linha == "10"
    assert exclusivos[0].beneficiario == "VALE3"
    assert exclusivos[0].valor == Decimal("19.50")


def test_rendimento_fii_goes_to_isentos_linha_26() -> None:
    isentos, exclusivos = map_proventos([_prov("HGRE11", "Rendimento", "63.00")])
    assert len(exclusivos) == 0
    assert len(isentos) == 1
    assert isentos[0].linha == "26"


def test_multiple_dividendos_same_ticker_are_accumulated() -> None:
    proventos = [
        _prov("ITSA4", "Dividendo", "20.00"),
        _prov("ITSA4", "Dividendo", "21.16"),
    ]
    isentos, _ = map_proventos(proventos)
    itsa4_entries = [r for r in isentos if r.beneficiario == "ITSA4"]
    assert len(itsa4_entries) == 1
    assert itsa4_entries[0].valor == Decimal("41.16")


def test_multiple_tickers_produce_separate_entries() -> None:
    proventos = [
        _prov("ITSA4", "Dividendo", "41.16"),
        _prov("VALE3", "Dividendo", "19.16"),
    ]
    isentos, _ = map_proventos(proventos)
    beneficiarios = {r.beneficiario for r in isentos}
    assert "ITSA4" in beneficiarios
    assert "VALE3" in beneficiarios


def test_empty_proventos_returns_empty_lists() -> None:
    isentos, exclusivos = map_proventos([])
    assert not isentos
    assert not exclusivos


def test_reembolsos_accumulated_per_ticker() -> None:
    reembolsos = [_reimb("TAEE11", "30.00"), _reimb("TAEE11", "35.23")]
    result = map_reembolsos(reembolsos)
    taee = [r for r in result if r.beneficiario == "TAEE11"]
    assert len(taee) == 1
    assert taee[0].valor == Decimal("65.23")


def test_reembolsos_different_tickers_separate_entries() -> None:
    reembolsos = [_reimb("TAEE11", "65.23"), _reimb("WEGE3", "1.37")]
    result = map_reembolsos(reembolsos)
    assert len(result) == 2


def test_reembolsos_empty_returns_empty() -> None:
    assert not map_reembolsos([])
