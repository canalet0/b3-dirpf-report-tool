from decimal import Decimal, InvalidOperation
from pathlib import Path

from contabilidade.models.b3 import (
    AcaoPosition,
    B3Report,
    EmprestimoPosition,
    EtfPosition,
    FundoPosition,
    Provento,
    Reembolso,
    RendaFixaPosition,
    TesouroDiretoPosition,
)
from contabilidade.parser.xlsx_reader import read_xlsx

_SHEET_ACOES = "Posição - Ações"
_SHEET_EMPRESTIMOS = "Posição - Empréstimos"
_SHEET_ETF = "Posição - ETF"
_SHEET_FUNDOS = "Posição - Fundos"
_SHEET_RENDA_FIXA = "Posição - Renda Fixa"
_SHEET_TESOURO = "Posição - Tesouro Direto"
_SHEET_PROVENTOS = "Proventos Recebidos"
_SHEET_REEMBOLSOS = "Reembolsos de Empréstimo"


def _to_decimal(value: str | None) -> Decimal:
    if value is None or value.strip() in ("-", "", "None"):
        return Decimal("0")
    raw = value.strip()
    # Determine format: if both '.' and ',' exist, the last one is decimal separator.
    # If only '.' exists (e.g. "143.85" from float->str), it's already decimal notation.
    # If only ',' exists (e.g. "1.270,19" BR format), '.' is thousands, ',' is decimal.
    if "," in raw and "." in raw:
        # BR format: "1.270,19" — remove '.' then replace ',' with '.'
        cleaned = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        # Just a comma decimal: "1270,19"
        cleaned = raw.replace(",", ".")
    else:
        # Already dot-decimal or integer: "143.85", "7", "1270.19"
        cleaned = raw
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _str(value: str | None) -> str:
    return value.strip() if value else ""


def _parse_acoes(rows: list[list[str | None]]) -> list[AcaoPosition]:
    # Skip header row (index 0)
    result: list[AcaoPosition] = []
    for row in rows[1:]:
        if len(row) < 14:
            continue
        if _str(row[0]) == "":
            continue
        result.append(
            AcaoPosition(
                produto=_str(row[0]),
                instituicao=_str(row[1]),
                conta=_str(row[2]),
                codigo_negociacao=_str(row[3]),
                cnpj_empresa=_str(row[4]),
                codigo_isin=_str(row[5]),
                tipo=_str(row[6]),
                escriturador=_str(row[7]),
                quantidade=_to_decimal(row[8]),
                quantidade_disponivel=_to_decimal(row[9]),
                preco_fechamento=_to_decimal(row[12]),
                valor_atualizado=_to_decimal(row[13]),
            )
        )
    return result


def _parse_emprestimos(rows: list[list[str | None]]) -> list[EmprestimoPosition]:
    result: list[EmprestimoPosition] = []
    for row in rows[1:]:
        if len(row) < 14:
            continue
        if _str(row[0]) == "":
            continue
        result.append(
            EmprestimoPosition(
                produto=_str(row[0]),
                instituicao=_str(row[1]),
                natureza=_str(row[2]),
                numero_contrato=_str(row[3]),
                taxa=_to_decimal(row[7]),
                data_registro=_str(row[9]),
                data_vencimento=_str(row[10]),
                quantidade=_to_decimal(row[11]),
                valor_atualizado=_to_decimal(row[13]),
            )
        )
    return result


def _parse_etfs(rows: list[list[str | None]]) -> list[EtfPosition]:
    result: list[EtfPosition] = []
    for row in rows[1:]:
        if len(row) < 13:
            continue
        if _str(row[0]) == "":
            continue
        result.append(
            EtfPosition(
                produto=_str(row[0]),
                instituicao=_str(row[1]),
                conta=_str(row[2]),
                codigo_negociacao=_str(row[3]),
                cnpj_fundo=_str(row[4]),
                codigo_isin=_str(row[5]),
                tipo=_str(row[6]),
                quantidade=_to_decimal(row[7]),
                preco_fechamento=_to_decimal(row[11]),
                valor_atualizado=_to_decimal(row[12]),
            )
        )
    return result


def _parse_fundos(rows: list[list[str | None]]) -> list[FundoPosition]:
    result: list[FundoPosition] = []
    for row in rows[1:]:
        if len(row) < 14:
            continue
        if _str(row[0]) == "":
            continue
        result.append(
            FundoPosition(
                produto=_str(row[0]),
                instituicao=_str(row[1]),
                conta=_str(row[2]),
                codigo_negociacao=_str(row[3]),
                cnpj_fundo=_str(row[4]),
                codigo_isin=_str(row[5]),
                tipo=_str(row[6]),
                administrador=_str(row[7]),
                quantidade=_to_decimal(row[8]),
                preco_fechamento=_to_decimal(row[12]),
                valor_atualizado=_to_decimal(row[13]),
            )
        )
    return result


def _parse_renda_fixa(rows: list[list[str | None]]) -> list[RendaFixaPosition]:
    result: list[RendaFixaPosition] = []
    for row in rows[1:]:
        if len(row) < 17:
            continue
        if _str(row[0]) == "":
            continue
        # Column indices: 0=Produto, 1=Instituição, 2=Emissor, 3=Código,
        # 4=Indexador, 5=Tipo de regime, 6=Data de Emissão, 7=Vencimento,
        # 8=Quantidade, 9=Qtd Disponível, 10=Qtd Indisponível, 11=Motivo,
        # 12=Contraparte, 13=Preço MTM, 14=Valor MTM, 15=Preço CURVA, 16=Valor CURVA
        result.append(
            RendaFixaPosition(
                produto=_str(row[0]),
                instituicao=_str(row[1]),
                emissor=_str(row[2]),
                codigo=_str(row[3]),
                indexador=_str(row[4]),
                tipo_regime=_str(row[5]),
                data_emissao=_str(row[6]),
                vencimento=_str(row[7]),
                quantidade=_to_decimal(row[8]),
                valor_atualizado_curva=_to_decimal(row[16]),
            )
        )
    return result


def _parse_tesouro_direto(rows: list[list[str | None]]) -> list[TesouroDiretoPosition]:
    result: list[TesouroDiretoPosition] = []
    for row in rows[1:]:
        if len(row) < 13:
            continue
        if _str(row[0]) == "":
            continue
        # Columns: 0=Produto, 1=Instituição, 2=Código ISIN, 3=Indexador,
        # 4=Vencimento, 5=Quantidade, 6=Qtd Disponível, 7=Qtd Indisponível,
        # 8=Motivo, 9=Valor Aplicado, 10=Valor bruto, 11=Valor líquido, 12=Valor Atualizado
        result.append(
            TesouroDiretoPosition(
                produto=_str(row[0]),
                instituicao=_str(row[1]),
                codigo_isin=_str(row[2]),
                indexador=_str(row[3]),
                vencimento=_str(row[4]),
                quantidade=_to_decimal(row[5]),
                valor_aplicado=_to_decimal(row[9]),
                valor_atualizado=_to_decimal(row[12]),
            )
        )
    return result


def _parse_proventos(rows: list[list[str | None]]) -> list[Provento]:
    result: list[Provento] = []
    for row in rows[1:]:
        if len(row) < 3:
            continue
        if _str(row[0]) == "":
            continue
        result.append(
            Provento(
                produto=_str(row[0]),
                tipo_evento=_str(row[1]),
                valor_liquido=_to_decimal(row[2]),
            )
        )
    return result


def _parse_reembolsos(rows: list[list[str | None]]) -> list[Reembolso]:
    result: list[Reembolso] = []
    for row in rows[1:]:
        if len(row) < 3:
            continue
        if _str(row[0]) == "":
            continue
        result.append(
            Reembolso(
                produto=_str(row[0]),
                tipo_evento=_str(row[1]),
                valor_liquido=_to_decimal(row[2]),
            )
        )
    return result


def parse_b3_report(year: int, path: Path) -> B3Report:
    sheets = read_xlsx(path)

    def get(name: str) -> list[list[str | None]]:
        return sheets.get(name, [])

    acoes_rows = get(_SHEET_ACOES)
    emprestimos_rows = get(_SHEET_EMPRESTIMOS)
    etfs_rows = get(_SHEET_ETF)
    fundos_rows = get(_SHEET_FUNDOS)
    renda_fixa_rows = get(_SHEET_RENDA_FIXA)
    tesouro_rows = get(_SHEET_TESOURO)
    proventos_rows = get(_SHEET_PROVENTOS)
    reembolsos_rows = get(_SHEET_REEMBOLSOS)

    return B3Report(
        year=year,
        acoes=_parse_acoes(acoes_rows) if len(acoes_rows) > 1 else [],
        emprestimos=(
            _parse_emprestimos(emprestimos_rows) if len(emprestimos_rows) > 1 else []
        ),
        etfs=_parse_etfs(etfs_rows) if len(etfs_rows) > 1 else [],
        fundos=_parse_fundos(fundos_rows) if len(fundos_rows) > 1 else [],
        renda_fixa=(
            _parse_renda_fixa(renda_fixa_rows) if len(renda_fixa_rows) > 1 else []
        ),
        tesouro_direto=(
            _parse_tesouro_direto(tesouro_rows) if len(tesouro_rows) > 1 else []
        ),
        proventos=_parse_proventos(proventos_rows) if len(proventos_rows) > 1 else [],
        reembolsos=(
            _parse_reembolsos(reembolsos_rows) if len(reembolsos_rows) > 1 else []
        ),
    )
