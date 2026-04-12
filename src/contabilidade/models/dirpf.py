from dataclasses import dataclass
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
class DirpfReport:
    year: int
    bens_e_direitos: list[BenDireito]
    rendimentos_isentos: list[RendimentoIsentoNaoTributavel]
    rendimentos_exclusivos: list[RendimentoTributacaoExclusiva]
    renda_variavel_notas: list[RendaVariavelNota]
