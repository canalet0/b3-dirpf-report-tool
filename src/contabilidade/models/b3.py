from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AcaoPosition:  # pylint: disable=too-many-instance-attributes
    produto: str
    instituicao: str
    conta: str
    codigo_negociacao: str
    cnpj_empresa: str
    codigo_isin: str
    tipo: str
    escriturador: str
    quantidade: Decimal
    quantidade_disponivel: Decimal
    preco_fechamento: Decimal
    valor_atualizado: Decimal


@dataclass(frozen=True)
class EmprestimoPosition:  # pylint: disable=too-many-instance-attributes
    produto: str
    instituicao: str
    natureza: str
    numero_contrato: str
    taxa: Decimal
    data_registro: str
    data_vencimento: str
    quantidade: Decimal
    valor_atualizado: Decimal


@dataclass(frozen=True)
class EtfPosition:  # pylint: disable=too-many-instance-attributes
    produto: str
    instituicao: str
    conta: str
    codigo_negociacao: str
    cnpj_fundo: str
    codigo_isin: str
    tipo: str
    quantidade: Decimal
    preco_fechamento: Decimal
    valor_atualizado: Decimal


@dataclass(frozen=True)
class FundoPosition:  # pylint: disable=too-many-instance-attributes
    produto: str
    instituicao: str
    conta: str
    codigo_negociacao: str
    cnpj_fundo: str
    codigo_isin: str
    tipo: str
    administrador: str
    quantidade: Decimal
    preco_fechamento: Decimal
    valor_atualizado: Decimal


@dataclass(frozen=True)
class RendaFixaPosition:  # pylint: disable=too-many-instance-attributes
    produto: str
    instituicao: str
    emissor: str
    codigo: str
    indexador: str
    tipo_regime: str
    data_emissao: str
    vencimento: str
    quantidade: Decimal
    valor_atualizado_curva: Decimal


@dataclass(frozen=True)
class TesouroDiretoPosition:  # pylint: disable=too-many-instance-attributes
    produto: str
    instituicao: str
    codigo_isin: str
    indexador: str
    vencimento: str
    quantidade: Decimal
    valor_aplicado: Decimal
    valor_atualizado: Decimal


@dataclass(frozen=True)
class Provento:
    produto: str
    tipo_evento: str
    valor_liquido: Decimal


@dataclass(frozen=True)
class Reembolso:
    produto: str
    tipo_evento: str
    valor_liquido: Decimal


@dataclass(frozen=True)
class B3Report:  # pylint: disable=too-many-instance-attributes
    year: int
    acoes: list[AcaoPosition]
    emprestimos: list[EmprestimoPosition]
    etfs: list[EtfPosition]
    fundos: list[FundoPosition]
    renda_fixa: list[RendaFixaPosition]
    tesouro_direto: list[TesouroDiretoPosition]
    proventos: list[Provento]
    reembolsos: list[Reembolso]
