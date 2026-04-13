_TIPO_DIVIDENDO = "dividendo"
_TIPO_JCP = "juros sobre capital"
_TIPO_RENDIMENTO_FII = "rendimento"


def classify_provento(tipo_evento: str) -> str:
    lower = tipo_evento.lower()
    if _TIPO_DIVIDENDO in lower:
        return "dividendo"
    if _TIPO_JCP in lower:
        return "jcp"
    if _TIPO_RENDIMENTO_FII in lower:
        return "rendimento_fii"
    return "outros"
