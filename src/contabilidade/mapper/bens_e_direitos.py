from decimal import Decimal

from contabilidade.models.b3 import (
    AcaoPosition,
    EtfPosition,
    FundoPosition,
    RendaFixaPosition,
    TesouroDiretoPosition,
)
from contabilidade.models.dirpf import BenDireito

_VALOR_ANTERIOR_NOTA = "[PREENCHER COM O VALOR DECLARADO NA DIRPF DO ANO ANTERIOR]"


def _brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_cnpj(raw: str) -> str:
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    return raw


def _ticker_from_produto(produto: str) -> tuple[str, str]:
    """Return (ticker, company_name) from 'TICKER - COMPANY NAME' format."""
    parts = produto.split(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return produto.strip(), produto.strip()


def map_acoes(acoes: list[AcaoPosition], year: int) -> list[BenDireito]:
    result: list[BenDireito] = []
    for acao in acoes:
        ticker, company = _ticker_from_produto(acao.produto)
        cnpj = _format_cnpj(acao.cnpj_empresa)
        discriminacao = (
            f"QUANTIDADE: {acao.quantidade} ações de {company} ({ticker} {acao.tipo}), "
            f"CNPJ {cnpj}, custodiadas em {acao.instituicao}, conta {acao.conta}. "
            f"Código ISIN: {acao.codigo_isin}. "
            f"Preço de fechamento em 31/12/{year}: {_brl(acao.preco_fechamento)}. "
            f"Valor de mercado em 31/12/{year}: {_brl(acao.valor_atualizado)}. "
            f"Situação em 31/12/{year - 1}: {_VALOR_ANTERIOR_NOTA}"
        )
        result.append(
            BenDireito(
                grupo="03",
                codigo="01",
                cnpj=cnpj,
                discriminacao=discriminacao,
                valor_anterior=Decimal("0"),
                valor_atual=acao.valor_atualizado,
            )
        )
    return result


def map_etfs(etfs: list[EtfPosition], year: int) -> list[BenDireito]:
    result: list[BenDireito] = []
    for etf in etfs:
        ticker, fund_name = _ticker_from_produto(etf.produto)
        cnpj = _format_cnpj(etf.cnpj_fundo)
        tipo_nota = f" [Tipo: {etf.tipo}]" if etf.tipo else ""
        discriminacao = (
            f"QUANTIDADE: {etf.quantidade} cotas de {fund_name} ({ticker}){tipo_nota}, "
            f"CNPJ do fundo {cnpj}, custodiadas em {etf.instituicao}, conta {etf.conta}. "
            f"Código ISIN: {etf.codigo_isin}. "
            f"Preço de fechamento em 31/12/{year}: {_brl(etf.preco_fechamento)}. "
            f"Valor de mercado em 31/12/{year}: {_brl(etf.valor_atualizado)}. "
            f"Situação em 31/12/{year - 1}: {_VALOR_ANTERIOR_NOTA}"
        )
        result.append(
            BenDireito(
                grupo="07",
                codigo="09",
                cnpj=cnpj,
                discriminacao=discriminacao,
                valor_anterior=Decimal("0"),
                valor_atual=etf.valor_atualizado,
            )
        )
    return result


def _is_fii(produto: str) -> bool:
    upper = produto.upper()
    return "IMOB" in upper or "FII" in upper or "FIAGRO" in upper


def map_fundos(fundos: list[FundoPosition], year: int) -> list[BenDireito]:
    result: list[BenDireito] = []
    for fundo in fundos:
        ticker, fund_name = _ticker_from_produto(fundo.produto)
        cnpj = _format_cnpj(fundo.cnpj_fundo)
        fii = _is_fii(fundo.produto)
        tipo_label = (
            "Fundo de Investimento Imobiliário (FII)"
            if fii
            else "Fundo de Investimento"
        )
        discriminacao = (
            f"QUANTIDADE: {fundo.quantidade} cotas de {fund_name} ({ticker}) — {tipo_label}, "
            f"CNPJ do fundo {cnpj}, administrado por {fundo.administrador}, "
            f"custodiado em {fundo.instituicao}, conta {fundo.conta}. "
            f"Código ISIN: {fundo.codigo_isin}. "
            f"Preço de fechamento em 31/12/{year}: {_brl(fundo.preco_fechamento)}. "
            f"Valor de mercado em 31/12/{year}: {_brl(fundo.valor_atualizado)}. "
            f"Situação em 31/12/{year - 1}: {_VALOR_ANTERIOR_NOTA}"
        )
        result.append(
            BenDireito(
                grupo="07",
                codigo="03",
                cnpj=cnpj,
                discriminacao=discriminacao,
                valor_anterior=Decimal("0"),
                valor_atual=fundo.valor_atualizado,
            )
        )
    return result


def _renda_fixa_codigo(produto: str) -> str:
    upper = produto.upper()
    if upper.startswith("DEB") or "DEBÊNTURE" in upper or "DEBENTURE" in upper:
        return "03"
    return "02"


def map_renda_fixa(renda_fixa: list[RendaFixaPosition], year: int) -> list[BenDireito]:
    result: list[BenDireito] = []
    for rf in renda_fixa:
        codigo = _renda_fixa_codigo(rf.produto)
        descricao_tipo = "Debênture" if codigo == "03" else "Título de Renda Fixa"
        discriminacao = (
            f"{descricao_tipo}: {rf.produto}. "
            f"Emissor: {rf.emissor}. "
            f"Código: {rf.codigo}. "
            f"Indexador: {rf.indexador}. "
            f"Tipo de regime: {rf.tipo_regime}. "
            f"Data de emissão: {rf.data_emissao}. "
            f"Vencimento: {rf.vencimento}. "
            f"Quantidade: {rf.quantidade}. "
            f"Custodiado em {rf.instituicao}. "
            f"Valor atualizado (curva) em 31/12/{year}: {_brl(rf.valor_atualizado_curva)}. "
            f"Situação em 31/12/{year - 1}: {_VALOR_ANTERIOR_NOTA}"
        )
        result.append(
            BenDireito(
                grupo="04",
                codigo=codigo,
                cnpj="",
                discriminacao=discriminacao,
                valor_anterior=Decimal("0"),
                valor_atual=rf.valor_atualizado_curva,
            )
        )
    return result


def map_tesouro_direto(
    tesouro: list[TesouroDiretoPosition], year: int
) -> list[BenDireito]:
    result: list[BenDireito] = []
    for td in tesouro:
        discriminacao = (
            f"Tesouro Direto: {td.produto}. "
            f"Código ISIN: {td.codigo_isin}. "
            f"Indexador: {td.indexador}. "
            f"Vencimento: {td.vencimento}. "
            f"Quantidade: {td.quantidade}. "
            f"Valor aplicado: {_brl(td.valor_aplicado)}. "
            f"Custodiado em {td.instituicao}. "
            f"Valor atualizado em 31/12/{year}: {_brl(td.valor_atualizado)}. "
            f"Situação em 31/12/{year - 1}: {_VALOR_ANTERIOR_NOTA}"
        )
        result.append(
            BenDireito(
                grupo="04",
                codigo="04",
                cnpj="",
                discriminacao=discriminacao,
                valor_anterior=Decimal("0"),
                valor_atual=td.valor_atualizado,
            )
        )
    return result
