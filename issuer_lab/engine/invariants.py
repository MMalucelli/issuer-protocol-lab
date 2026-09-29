from __future__ import annotations

from dataclasses import dataclass

from issuer_lab.domain.models import EPS, IssuerState


@dataclass(frozen=True)
class InvariantViolation:
    code: str
    message: str


class InvariantError(RuntimeError):
    def __init__(self, violations: list[InvariantViolation]):
        self.violations = violations
        super().__init__("; ".join(f"{v.code}: {v.message}" for v in violations))


def check_state(state: IssuerState) -> list[InvariantViolation]:
    out: list[InvariantViolation] = []
    if state.treasury < -EPS:
        out.append(InvariantViolation("TREASURY_NEGATIVE", "Treasury must remain non-negative."))

    c, q = state.capacity, state.thresholds
    for name in ("gross", "net_plus", "net_minus"):
        if getattr(q, name) - getattr(c, name) > EPS:
            out.append(InvariantViolation("Q_EXCEEDS_H", f"Q_{name} exceeds H_{name}."))

    w = state.active_window
    if w:
        if abs(w.gross - (w.buy + w.sell)) > EPS:
            out.append(InvariantViolation("GROSS_IDENTITY", "Gross must equal BUY + SELL."))
        if abs(w.net - (w.buy - w.sell)) > EPS:
            out.append(InvariantViolation("NET_IDENTITY", "Net must equal BUY - SELL."))
        if w.gross - w.capacity.gross > EPS:
            out.append(InvariantViolation("H_GROSS_EXCEEDED", "Gross exceeds H_gross."))
        if w.net_plus - w.capacity.net_plus > EPS:
            out.append(InvariantViolation("H_NET_PLUS_EXCEEDED", "Positive Net exceeds H_net+."))
        if w.net_minus - w.capacity.net_minus > EPS:
            out.append(InvariantViolation("H_NET_MINUS_EXCEEDED", "Negative Net exceeds H_net-."))
        if w.sell - (w.initial_treasury + w.buy) > EPS:
            out.append(InvariantViolation("SELL_EXCEEDS_TREASURY", "SELL exceeds Treasury available during the window."))
    return out


def assert_state(state: IssuerState) -> None:
    violations = check_state(state)
    if violations:
        raise InvariantError(violations)
