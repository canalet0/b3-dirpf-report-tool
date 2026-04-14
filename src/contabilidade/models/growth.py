from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class YearSnapshot:
    # pylint: disable=too-many-instance-attributes
    year: int
    acoes: Decimal
    etfs: Decimal
    fundos: Decimal
    renda_fixa: Decimal
    tesouro: Decimal
    total: Decimal
    proventos: Decimal
    reembolsos: Decimal
    total_income: Decimal


@dataclass(frozen=True)
class YearGrowth:
    # pylint: disable=too-many-instance-attributes
    year: int
    total: Decimal
    abs_change: Decimal | None
    pct_change: Decimal | None
    pct_acoes: Decimal
    pct_etfs: Decimal
    pct_fundos: Decimal
    pct_renda_fixa: Decimal
    pct_tesouro: Decimal


@dataclass(frozen=True)
class MonthlyIncome:
    month: str
    valor: Decimal


@dataclass(frozen=True)
class GrowthReport:
    years: list[YearSnapshot]
    growth: list[YearGrowth]
    monthly_income: list[MonthlyIncome]
    has_movimentacao: bool
