from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AssetPerformance:
    ticker: str
    nome: str
    asset_class: str  # "acao"|"etf"|"fundo_fii"|"fundo"|"renda_fixa"|"tesouro"
    current_value: Decimal
    cost_basis: Decimal | None  # avg_price * qty from movimentacao; None if unavailable
    total_return: Decimal | None  # current_value - cost_basis
    total_return_pct: Decimal | None  # (total_return / cost_basis) * 100


@dataclass(frozen=True)
class DividendYield:
    ticker: str
    nome: str
    proventos_ano: Decimal
    current_value: Decimal
    yield_pct: Decimal | None  # None when current_value == 0


@dataclass(frozen=True)
class CostBasisEntry:
    ticker: str
    nome: str
    avg_price: Decimal
    quantity: Decimal
    total_cost: Decimal


@dataclass(frozen=True)
class AllocationBreakdown:  # pylint: disable=too-many-instance-attributes
    year: int
    acoes: Decimal
    fiis: Decimal
    fundos: Decimal
    etfs: Decimal
    renda_fixa: Decimal
    tesouro: Decimal
    total: Decimal
    pct_acoes: Decimal
    pct_fiis: Decimal
    pct_fundos: Decimal
    pct_etfs: Decimal
    pct_renda_fixa: Decimal
    pct_tesouro: Decimal


@dataclass(frozen=True)
class ClassPerformance:
    asset_class: str
    current_value: Decimal
    cost_basis: Decimal | None
    total_return: Decimal | None
    total_return_pct: Decimal | None


@dataclass(frozen=True)
class OverallPerformance:
    total_current: Decimal
    total_cost: Decimal | None  # None when no position has a known cost basis
    total_return: Decimal | None
    total_return_pct: Decimal | None
    by_class: list[ClassPerformance]


@dataclass(frozen=True)
class AnalyticsReport:
    year: int
    has_movimentacao: bool
    overall_performance: OverallPerformance
    performance: list[AssetPerformance]
    dividend_yields: list[DividendYield]
    cost_basis: list[CostBasisEntry]
    allocation: AllocationBreakdown
