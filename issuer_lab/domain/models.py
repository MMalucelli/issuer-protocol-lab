from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


EPS = 1e-9


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class CapacityDimension(str, Enum):
    GROSS = "gross"
    NET_PLUS = "net_plus"
    NET_MINUS = "net_minus"


@dataclass(frozen=True)
class Capacity:
    gross: float
    net_plus: float
    net_minus: float

    def __post_init__(self) -> None:
        if min(self.gross, self.net_plus, self.net_minus) < 0:
            raise ValueError("capacity cannot be negative")
        if self.gross + EPS < max(self.net_plus, self.net_minus):
            raise ValueError("H_gross must be >= both directional Net capacities")


@dataclass(frozen=True)
class Thresholds:
    gross: float
    net_plus: float
    net_minus: float

    def __post_init__(self) -> None:
        if min(self.gross, self.net_plus, self.net_minus) < 0:
            raise ValueError("threshold cannot be negative")

    @classmethod
    def from_rho(cls, capacity: Capacity, *, gross: float, net_plus: float, net_minus: float) -> "Thresholds":
        rhos = (gross, net_plus, net_minus)
        if any(r <= 0 or r > 1 for r in rhos):
            raise ValueError("rho must satisfy 0 < rho <= 1")
        return cls(capacity.gross * gross, capacity.net_plus * net_plus, capacity.net_minus * net_minus)


@dataclass(frozen=True)
class Execution:
    timestamp: datetime
    side: Side
    quantity: float
    price: float

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")


@dataclass
class WindowState:
    window_id: str
    opened_at: datetime
    initial_treasury: float
    capacity: Capacity
    thresholds: Thresholds
    buy: float = 0.0
    sell: float = 0.0
    gross: float = 0.0
    net: float = 0.0
    # Historical intraday alerts and alerts that remain above Q right now.
    q_crossed: set[CapacityDimension] = field(default_factory=set)
    q_active: set[CapacityDimension] = field(default_factory=set)
    executions: list[Execution] = field(default_factory=list)

    @property
    def net_plus(self) -> float:
        return max(self.net, 0.0)

    @property
    def net_minus(self) -> float:
        return max(-self.net, 0.0)

    def utilization(self, dimension: CapacityDimension) -> float:
        used = {
            CapacityDimension.GROSS: self.gross,
            CapacityDimension.NET_PLUS: self.net_plus,
            CapacityDimension.NET_MINUS: self.net_minus,
        }[dimension]
        cap = {
            CapacityDimension.GROSS: self.capacity.gross,
            CapacityDimension.NET_PLUS: self.capacity.net_plus,
            CapacityDimension.NET_MINUS: self.capacity.net_minus,
        }[dimension]
        return 0.0 if cap <= EPS else used / cap

    def disclosure_dimensions(self) -> set[CapacityDimension]:
        """Dimensions that require disclosure if the window closes now."""
        values = {
            CapacityDimension.GROSS: (self.gross, self.thresholds.gross),
            CapacityDimension.NET_PLUS: (self.net_plus, self.thresholds.net_plus),
            CapacityDimension.NET_MINUS: (self.net_minus, self.thresholds.net_minus),
        }
        return {dimension for dimension, (used, q) in values.items() if used + EPS >= q}


@dataclass
class IssuerState:
    issuer_id: str
    ticker: str
    treasury: float
    capacity: Capacity
    thresholds: Thresholds
    active_window: WindowState | None = None
    version: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.treasury < 0:
            raise ValueError("treasury cannot be negative")
