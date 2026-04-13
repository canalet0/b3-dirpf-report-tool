from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class BenDireito:
    grupo: str
    codigo: str
    cnpj: str
    discriminacao: str
    valor_anterior: Decimal
    valor_atual: Decimal


@dataclass(frozen=True)
class RendimentoIsentoNaoTributavel:
    linha: str
    tipo: str
    beneficiario: str
    valor: Decimal
    observacao: str


@dataclass(frozen=True)
class RendimentoTributacaoExclusiva:
    linha: str
    tipo: str
    beneficiario: str
    cnpj_fonte: str
    valor: Decimal
    observacao: str


@dataclass(frozen=True)
class RendaVariavelNota:
    mensagem: str


@dataclass(frozen=True)
class OperacaoRendaVariavel:  # pylint: disable=too-many-instance-attributes,too-many-positional-arguments
    mes: str  # "2024-03"
    ticker: str
    nome: str
    tipo: str  # "Venda" | "Compra"
    data: str
    quantidade: Decimal
    preco_unitario: Decimal | None
    valor_operacao: Decimal | None
    custo_medio: Decimal | None
    ganho_estimado: Decimal | None


@dataclass(frozen=True)
class ResumoMensalRendaVariavel:
    mes: str  # "2024-03"
    mes_label: str  # "Março/2024"
    total_vendas: Decimal | None  # None if any sell has "-" price
    total_ganho_estimado: Decimal | None
    isento: bool | None  # None when total_vendas unknown
    tickers_vendidos: list[str]
    operacoes: list[OperacaoRendaVariavel]


@dataclass(frozen=True)
class EventoCorporativo:
    data: str
    ticker: str
    nome: str
    tipo: str
    quantidade: Decimal | None
    observacao: str


@dataclass(frozen=True)
class DirpfReport:  # pylint: disable=too-many-instance-attributes
    year: int
    bens_e_direitos: list[BenDireito]
    rendimentos_isentos: list[RendimentoIsentoNaoTributavel]
    rendimentos_exclusivos: list[RendimentoTributacaoExclusiva]
    renda_variavel_notas: list[RendaVariavelNota]
    renda_variavel_operacoes: list[ResumoMensalRendaVariavel] = field(
        default_factory=list
    )
    eventos_corporativos: list[EventoCorporativo] = field(default_factory=list)
    income_reconciliation: list[str] = field(default_factory=list)
