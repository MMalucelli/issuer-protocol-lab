from datetime import datetime, timezone

import pytest

from issuer_lab import Capacity, CapacityDimension, IssuerState, RuleViolation, Side, StateEngine, Thresholds
from issuer_lab.domain.events import EventType


def t(minute=0):
    return datetime(2026, 9, 15, 14, minute, tzinfo=timezone.utc)


def engine(treasury=100.0, gross=200.0, plus=150.0, minus=80.0, rho=.5):
    h = Capacity(gross, plus, minus)
    q = Thresholds.from_rho(h, gross=rho, net_plus=rho, net_minus=rho)
    return StateEngine(IssuerState("issuer-1", "TEST3", treasury, h, q))


def test_buy_updates_gross_net_and_treasury():
    e = engine()
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 40, 10)
    w = e.state.active_window
    assert (w.buy, w.sell, w.gross, w.net) == (40, 0, 40, 40)
    assert e.state.treasury == 140


def test_reversal_reduces_net_but_never_gross():
    e = engine()
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 60, 10)
    e.execute(t(2), Side.SELL, 60, 11)
    w = e.state.active_window
    assert w.net == 0
    assert w.gross == 120
    assert e.state.treasury == 100


def test_sell_cannot_exceed_treasury():
    e = engine(treasury=10)
    e.open_window(t(), "W1")
    with pytest.raises(RuleViolation, match="Treasury"):
        e.execute(t(1), Side.SELL, 11, 10)


def test_gross_cap_is_hard_even_when_net_offsets():
    e = engine(gross=100, plus=100, minus=100)
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 50, 10)
    e.execute(t(2), Side.SELL, 50, 10)
    with pytest.raises(RuleViolation, match="H_gross"):
        e.execute(t(3), Side.BUY, 1, 10)


def test_directional_net_caps_are_independent():
    e = engine(treasury=200, gross=500, plus=30, minus=20)
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 30, 10)
    with pytest.raises(RuleViolation, match=r"H_net\+"):
        e.execute(t(2), Side.BUY, 1, 10)

    e2 = engine(treasury=200, gross=500, plus=30, minus=20)
    e2.open_window(t(), "W1")
    e2.execute(t(1), Side.SELL, 20, 10)
    with pytest.raises(RuleViolation, match="H_net-"):
        e2.execute(t(2), Side.SELL, 1, 10)


def test_max_executable_quantity_respects_gross_and_net_plus():
    e = engine(treasury=100, gross=100, plus=60, minus=40)
    e.open_window(t(), "W1")
    assert e.max_executable_quantity(Side.BUY) == 60
    e.execute(t(1), Side.BUY, 50, 10)
    assert e.max_executable_quantity(Side.BUY) == 10
    assert e.execution_limits(Side.BUY) == {"gross": 50, "net_plus": 10}


def test_max_executable_sell_respects_treasury_and_directional_reversal():
    e = engine(treasury=25, gross=200, plus=100, minus=40)
    e.open_window(t(), "W1")
    assert e.max_executable_quantity(Side.SELL) == 25
    e.execute(t(1), Side.BUY, 30, 10)
    # The existing long position can be reversed before H_net- becomes binding.
    assert e.max_executable_quantity(Side.SELL) == 55


def test_q_is_trigger_not_execution_amount_or_cap():
    e = engine(gross=200, plus=200, minus=200, rho=.5)
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 120, 10)
    q_events = [x for x in e.events if x.event_type is EventType.Q_CROSSED]
    plus = next(x for x in q_events if x.payload["dimension"] == CapacityDimension.NET_PLUS.value)
    assert plus.payload["q"] == 100
    assert plus.payload["actual"] == 120
    assert e.state.active_window.net == 120


def test_fragmentation_crosses_q_only_once_and_does_not_reset_h():
    e = engine(gross=200, plus=200, minus=200, rho=.5)
    e.open_window(t(), "W1")
    for i in range(1, 6):
        e.execute(t(i), Side.BUY, 25, 10)
    q_plus = [x for x in e.events if x.event_type is EventType.Q_CROSSED and x.payload["dimension"] == "net_plus"]
    assert len(q_plus) == 1
    assert e.state.active_window.capacity.net_plus == 200
    assert e.state.active_window.net == 125


def test_threshold_cannot_exceed_capacity():
    h = Capacity(100, 100, 100)
    q = Thresholds(101, 50, 50)
    with pytest.raises(Exception):
        StateEngine(IssuerState("x", "X3", 0, h, q))


def test_event_log_is_sequential_and_reconstructible_at_basic_level():
    e = engine()
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 20, 10)
    e.close_window(t(2), "test")
    assert [x.sequence for x in e.events] == list(range(1, len(e.events) + 1))
    assert e.events[0].event_type is EventType.WINDOW_OPENED
    assert e.events[-1].event_type is EventType.WINDOW_CLOSED


def test_net_q_crossing_is_an_alert_and_can_clear_before_close():
    e = engine(treasury=200, gross=500, plus=200, minus=200, rho=.5)
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 120, 10)
    e.execute(t(2), Side.SELL, 30, 10)

    w = e.state.active_window
    assert CapacityDimension.NET_PLUS in w.q_crossed
    assert CapacityDimension.NET_PLUS not in w.q_active
    assert any(x.event_type is EventType.Q_RETURNED_BELOW for x in e.events)

    closed = e.close_window(t(3), "end_of_day")
    evaluation = next(x for x in e.events if x.event_type is EventType.DISCLOSURE_EVALUATED)
    assert CapacityDimension.NET_PLUS not in closed.disclosure_dimensions()
    assert evaluation.payload["required"] is False


def test_no_disclosure_when_only_net_q_was_crossed_intraday_then_cleared():
    h = Capacity(1000, 200, 200)
    q = Thresholds.from_rho(h, gross=.9, net_plus=.5, net_minus=.5)
    e = StateEngine(IssuerState("issuer-1", "TEST3", 200, h, q))
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 120, 10)
    e.execute(t(2), Side.SELL, 30, 10)
    e.close_window(t(3), "end_of_day")

    evaluation = next(x for x in e.events if x.event_type is EventType.DISCLOSURE_EVALUATED)
    assert evaluation.payload["required"] is False
    assert evaluation.payload["dimensions"] == []
    assert evaluation.payload["q_alerted_intraday"] == ["net_plus"]


def test_gross_q_cannot_be_reversed_by_offsetting_trade():
    e = engine(treasury=200, gross=200, plus=200, minus=200, rho=.5)
    e.open_window(t(), "W1")
    e.execute(t(1), Side.BUY, 60, 10)
    e.execute(t(2), Side.SELL, 60, 10)
    e.close_window(t(3), "end_of_day")

    evaluation = next(x for x in e.events if x.event_type is EventType.DISCLOSURE_EVALUATED)
    assert evaluation.payload["required"] is True
    assert evaluation.payload["dimensions"] == ["gross"]
