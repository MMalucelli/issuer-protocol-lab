from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from issuer_lab.domain.events import DomainEvent, EventType
from issuer_lab.domain.models import (
    EPS, CapacityDimension, Execution, IssuerState, Side, WindowState,
)
from issuer_lab.engine.invariants import assert_state


class RuleViolation(ValueError):
    pass


class StateEngine:
    """Deterministic Milestone-1 engine: state + event -> next state."""

    def __init__(self, initial_state: IssuerState) -> None:
        self.state = deepcopy(initial_state)
        assert_state(self.state)
        self.events: list[DomainEvent] = []

    def _emit(self, event_type: EventType, timestamp: datetime, **payload) -> DomainEvent:
        event = DomainEvent(len(self.events) + 1, event_type, timestamp, payload)
        self.events.append(event)
        return event

    def open_window(self, timestamp: datetime, window_id: str) -> WindowState:
        if self.state.active_window is not None:
            raise RuleViolation("an active window already exists")
        self.state.active_window = WindowState(
            window_id=window_id,
            opened_at=timestamp,
            initial_treasury=self.state.treasury,
            capacity=self.state.capacity,
            thresholds=self.state.thresholds,
        )
        self.state.version += 1
        self._emit(EventType.WINDOW_OPENED, timestamp, window_id=window_id)
        assert_state(self.state)
        return deepcopy(self.state.active_window)

    def execute(self, timestamp: datetime, side: Side, quantity: float, price: float) -> Execution:
        w = self.state.active_window
        if w is None:
            raise RuleViolation("no active window")
        execution = Execution(timestamp, side, quantity, price)

        next_buy = w.buy + (quantity if side is Side.BUY else 0.0)
        next_sell = w.sell + (quantity if side is Side.SELL else 0.0)
        next_gross = next_buy + next_sell
        next_net = next_buy - next_sell

        if side is Side.SELL and quantity - self.state.treasury > EPS:
            raise RuleViolation("SELL exceeds current Treasury")
        if next_gross - w.capacity.gross > EPS:
            raise RuleViolation("execution exceeds H_gross")
        if max(next_net, 0.0) - w.capacity.net_plus > EPS:
            raise RuleViolation("execution exceeds H_net+")
        if max(-next_net, 0.0) - w.capacity.net_minus > EPS:
            raise RuleViolation("execution exceeds H_net-")

        w.buy, w.sell, w.gross, w.net = next_buy, next_sell, next_gross, next_net
        w.executions.append(execution)
        self.state.treasury += quantity if side is Side.BUY else -quantity
        self.state.version += 1
        self._emit(EventType.TRADE_EXECUTED, timestamp, side=side.value, quantity=quantity, price=price)
        self._update_q_alerts(timestamp)
        self._detect_h_exhaustion(timestamp)
        assert_state(self.state)
        return execution

    def execution_limits(self, side: Side) -> dict[str, float]:
        """Return the remaining executable quantity under each applicable hard limit."""
        w = self.state.active_window
        if w is None:
            raise RuleViolation("no active window")
        limits={"gross":max(0.0,w.capacity.gross-w.gross)}
        if side is Side.BUY:
            limits["net_plus"]=max(0.0,w.capacity.net_plus-w.net)
        else:
            limits["net_minus"]=max(0.0,w.capacity.net_minus+w.net)
            limits["treasury"]=max(0.0,self.state.treasury)
        return limits

    def max_executable_quantity(self, side: Side) -> float:
        """Maximum next fill that preserves every hard-cap invariant."""
        return min(self.execution_limits(side).values())

    def _update_q_alerts(self, timestamp: datetime) -> None:
        w = self.state.active_window
        assert w is not None
        values = {
            CapacityDimension.GROSS: (w.gross, w.thresholds.gross),
            CapacityDimension.NET_PLUS: (w.net_plus, w.thresholds.net_plus),
            CapacityDimension.NET_MINUS: (w.net_minus, w.thresholds.net_minus),
        }
        for dimension, (used, threshold) in values.items():
            above = used + EPS >= threshold
            if above and dimension not in w.q_active:
                w.q_active.add(dimension)
                w.q_crossed.add(dimension)
                self._emit(EventType.Q_CROSSED, timestamp, dimension=dimension.value, actual=used, q=threshold, utilization=w.utilization(dimension), effect="intraday_alert")
            elif not above and dimension in w.q_active:
                w.q_active.remove(dimension)
                self._emit(EventType.Q_RETURNED_BELOW, timestamp, dimension=dimension.value, actual=used, q=threshold, utilization=w.utilization(dimension), effect="intraday_alert_cleared")

    def _detect_h_exhaustion(self, timestamp: datetime) -> None:
        w = self.state.active_window
        assert w is not None
        values = {
            CapacityDimension.GROSS: (w.gross, w.capacity.gross),
            CapacityDimension.NET_PLUS: (w.net_plus, w.capacity.net_plus),
            CapacityDimension.NET_MINUS: (w.net_minus, w.capacity.net_minus),
        }
        for dimension, (used, cap) in values.items():
            if cap > EPS and abs(used - cap) <= EPS:
                already = any(e.event_type is EventType.H_EXHAUSTED and e.payload.get("dimension") == dimension.value for e in self.events)
                if not already:
                    self._emit(EventType.H_EXHAUSTED, timestamp, dimension=dimension.value, used=used, h=cap)

    def close_window(self, timestamp: datetime, reason: str = "manual") -> WindowState:
        if self.state.active_window is None:
            raise RuleViolation("no active window")
        closed = deepcopy(self.state.active_window)
        disclosure_dimensions=closed.disclosure_dimensions()
        self.state.active_window = None
        self.state.version += 1
        self._emit(
            EventType.DISCLOSURE_EVALUATED,
            timestamp,
            window_id=closed.window_id,
            required=bool(disclosure_dimensions),
            dimensions=sorted(dimension.value for dimension in disclosure_dimensions),
            gross=closed.gross,
            net=closed.net,
            q_alerted_intraday=sorted(dimension.value for dimension in closed.q_crossed),
        )
        self._emit(EventType.WINDOW_CLOSED, timestamp, window_id=closed.window_id, reason=reason, gross=closed.gross, net=closed.net)
        assert_state(self.state)
        return closed
