from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    WINDOW_OPENED = "WindowOpened"
    TRADE_EXECUTED = "TradeExecuted"
    Q_CROSSED = "QCrossed"
    Q_RETURNED_BELOW = "QReturnedBelow"
    DISCLOSURE_EVALUATED = "DisclosureEvaluated"
    H_EXHAUSTED = "HExhausted"
    WINDOW_CLOSED = "WindowClosed"


@dataclass(frozen=True)
class DomainEvent:
    sequence: int
    event_type: EventType
    timestamp: datetime
    payload: dict[str, Any] = field(default_factory=dict)
