from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MovimentacaoRow:  # pylint: disable=too-many-instance-attributes
    entrada_saida: str
    data: str  # "DD/MM/YYYY"
    movimentacao: str
    produto: str  # "TICKER - Company Name"
    instituicao: str
    quantidade: Decimal | None  # None when cell is "-"
    preco_unitario: Decimal | None
    valor_operacao: Decimal | None


@dataclass(frozen=True)
class MovimentacaoReport:
    year: int
    rows: list[MovimentacaoRow]
