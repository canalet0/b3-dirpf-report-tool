from decimal import Decimal

from contabilidade.mapper._income_categories import classify_provento
from contabilidade.models.b3 import Provento, Reembolso

_CATEGORY_LABELS = {
    "dividendo": "Dividendos",
    "jcp": "JCP",
    "rendimento_fii": "Rendimentos FII",
    "outros": "Outros rendimentos",
    "reembolso": "Reembolsos (BTC)",
}


def reconcile_income(
    proventos: list[Provento],
    reembolsos: list[Reembolso],
    movimentacao_income: dict[str, Decimal],
) -> list[str]:
    # Aggregate proventos by category
    prov_totals: dict[str, Decimal] = {}
    for p in proventos:
        cat = classify_provento(p.tipo_evento)
        prov_totals[cat] = prov_totals.get(cat, Decimal("0")) + p.valor_liquido

    # Reembolsos are their own category
    reimb_total = sum(r.valor_liquido for r in reembolsos)
    if reimb_total:
        prov_totals["reembolso"] = reimb_total

    # All categories mentioned in either source
    all_categories = set(prov_totals.keys()) | set(movimentacao_income.keys())

    messages: list[str] = []
    for cat in sorted(all_categories):
        label = _CATEGORY_LABELS.get(cat, cat)
        prov_val = prov_totals.get(cat, Decimal("0"))
        mov_val = movimentacao_income.get(cat, Decimal("0"))

        if prov_val == mov_val:
            messages.append(
                f"✓ {label}: {_brl(prov_val)} (proventos) == {_brl(mov_val)} (movimentação)"
            )
        else:
            diff = abs(prov_val - mov_val)
            messages.append(
                f"⚠ {label}: {_brl(prov_val)} (proventos) vs {_brl(mov_val)} (movimentação)"
                f" — diferença de {_brl(diff)}"
            )

    return messages


def _brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")
