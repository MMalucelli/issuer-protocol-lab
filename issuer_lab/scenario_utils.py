from __future__ import annotations

import math
from typing import Any, Iterable


def _number(value: Any) -> float:
    try:
        number = 0.0 if value is None else float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) and number >= 0 else 0.0


def editor_records_to_actions(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve incomplete editor rows while normalizing their shape."""
    actions = []
    for row in records:
        actions.append({
            "side": "SELL" if row.get("Operação") == "Venda" else "BUY",
            "quantity": _number(row.get("Quantidade")),
            "price": _number(row.get("Preço")),
            "time": str(row.get("Momento") or ""),
            "note": str(row.get("Observação") or ""),
        })
    return actions


def apply_editor_delta(actions: Iterable[dict[str, Any]], delta: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Apply a Streamlit data-editor delta before its rerun rebuilds the widget.

    Streamlit stores only the changed cells/rows in the widget state. Applying
    that delta to the persisted actions avoids replacing a freshly edited cell
    with the pre-rerun dataframe value.
    """
    rows = [
        {
            "Momento": action.get("time", ""),
            "Operação": "Venda" if action.get("side") == "SELL" else "Compra",
            "Quantidade": action.get("quantity", 0.0),
            "Preço": action.get("price", 0.0),
            "Observação": action.get("note", ""),
        }
        for action in actions
    ]
    delta = delta if isinstance(delta, dict) else {}

    for raw_index, changes in (delta.get("edited_rows") or {}).items():
        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            continue
        if 0 <= index < len(rows) and isinstance(changes, dict):
            rows[index].update(changes)

    deleted = []
    for raw_index in delta.get("deleted_rows") or []:
        try:
            deleted.append(int(raw_index))
        except (TypeError, ValueError):
            continue
    for index in sorted(set(deleted), reverse=True):
        if 0 <= index < len(rows):
            rows.pop(index)

    for added in delta.get("added_rows") or []:
        if isinstance(added, dict):
            rows.append(added)

    return editor_records_to_actions(rows)


def executable_actions(actions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only complete orders accepted by the simulation engine."""
    executable = []
    for action in actions:
        quantity = _number(action.get("quantity"))
        price = _number(action.get("price"))
        if quantity <= 0 or price <= 0:
            continue
        executable.append({**action, "side": "SELL" if action.get("side") == "SELL" else "BUY", "quantity": quantity, "price": price})
    return executable


def available_comparison_pairs(pairs, detail):
    """Keep only combinations whose evaluation completed successfully."""
    return [pair for pair in pairs if pair in detail]


def semantic_field_options(numeric_fields, *saved_fields):
    """Keep saved semantic mappings selectable during transient unresolved reruns."""
    options=[None]
    for field in [*numeric_fields,*saved_fields]:
        if field is not None and field not in options:
            options.append(field)
    return options


def comparison_projection(exposure: Any, capacity: Any, threshold_ratio: Any, *, normalized: bool) -> dict[str, float]:
    """Project a comparison into the domain of its fixed axis.

    A fixed scenario preserves absolute shares while specifications vary. A
    fixed specification preserves utilization while scenarios vary.
    """
    used = _number(exposure)
    h = _number(capacity)
    rho = _number(threshold_ratio)
    return {
        "value": used / h if normalized and h else (0.0 if normalized else used),
        "h_axis": 1.0 if normalized else h,
        "q_axis": rho if normalized else h * rho,
        "utilization": used / h if h else 0.0,
        "h_absolute": h,
        "q_absolute": h * rho,
        "q_ratio": rho,
    }
