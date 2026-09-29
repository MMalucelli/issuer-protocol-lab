from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any
from uuid import uuid4

PROJECT_SCHEMA = 3
HISTORY_LIMIT = 20
ENGINE_VERSION = "0.45.2"

FOUNDATION_KEYS = ("base_table", "base_provenance", "derived_defs", "source_specs", "semantic_mappings")
MEMORY_KEYS = ("signal_expr", "update_expr", "decay_expr", "I_MULT", "GAIN", "LAMBDA", "ACCEL", "REV_PENALTY")
CAPACITY_KEYS = ("h0_gross_expr", "h0_plus_expr", "h0_minus_expr", "hmax_expr", "sat_kind", "sat_shape")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _history() -> dict[str, list[dict[str, Any]]]:
    return {"undo": [], "redo": []}


def _ensure_v39_negative_scenario(project: dict[str, Any]) -> None:
    """Install the v0.39 review scenario once without overwriting user edits."""
    migrations = project.setdefault("migrations", {})
    migration_key = "v39_negative_scenario"
    if migrations.get(migration_key):
        return
    scenario_owner = project.get("scenarios", {})
    scenarios = scenario_owner.get("items", {})
    rows = project.get("foundation", {}).get("state", {}).get("base_table", [])
    has_pet4 = any(str(row.get("main_id", "")).strip().upper() == "PETR4" for row in rows)
    has_completed_specification = bool(project.get("experiments", {}).get("completed", {}))
    if not (scenarios and has_pet4 and has_completed_specification):
        return
    scenario_id = "pet4_venda_liquida_limite"
    scenarios.setdefault(scenario_id, {
        "id": scenario_id,
        "company": "PETR4",
        "strategy": "Venda líquida até o limite",
        "description": "Teste de Net negativo: cruza Q net−, atinge H net− e rejeita o excedente da segunda venda.",
        "actions": [
            {"time": "10:30", "side": "SELL", "quantity": 60000.0, "price": 38.5, "note": "Cruza Q net− mantendo saldo executável"},
            {"time": "15:30", "side": "SELL", "quantity": 50000.0, "price": 38.5, "note": "Excede H net−; executa o residual e rejeita o excedente"},
        ],
        "created_at": _now(),
        "updated_at": _now(),
        "derived_from": None,
        "history": _history(),
    })
    migrations[migration_key] = True


def adopt_global_treasury_mapping(project: dict[str, Any]) -> int:
    """Retire the legacy 80k override once Treasury has a global mapping.

    Older sample specifications inherited 80,000 as if it were a deliberate
    per-specification override.  It was actually the former default.  Explicit
    overrides created in the new UI carry ``treasury_override_explicit`` and
    are therefore preserved.
    """
    mappings = project.get("foundation", {}).get("state", {}).get("semantic_mappings", {})
    if not mappings.get("treasury"):
        return 0
    migrations = project.setdefault("migrations", {})
    migration_key = "v42_global_treasury_override_cleanup"
    if migrations.get(migration_key):
        return 0
    changed = 0
    for collection in ("drafts", "completed", "archived"):
        for experiment in project.get("experiments", {}).get(collection, {}).values():
            iw = experiment.get("config", {}).get("intrawindow", {})
            if iw.get("treasury_override_enabled") and not iw.get("treasury_override_explicit", False):
                iw["treasury_override_enabled"] = False
                changed += 1
    migrations[migration_key] = True
    return changed


def _numeric_columns(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    metadata = {"main_id", "__base_origin__", "__base_detail__"}
    out = []
    for key in rows[0]:
        if key in metadata:
            continue
        values = [row.get(key) for row in rows if row.get(key) is not None]
        if values and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
            out.append(key)
    return out


def _legacy_experiment(raw: dict[str, Any]) -> dict[str, Any]:
    configs = raw.get("configs", {})
    active_name = raw.get("iw_config") if raw.get("iw_config") in configs else next(iter(configs), "Configuração inicial")
    selected = configs.get(active_name, {})
    rows = list(raw.get("base_table", []))
    numeric = _numeric_columns(rows)
    float_field = next((name for name in numeric if "FLOAT" in name.upper()), None)
    price_field = next((name for name in numeric if name.upper() in {"LAST_PRICE", "PRICE", "CURRENT_PRICE", "PRECO_ATUAL"}), None)
    scenario_id = "cenario_principal"
    config = {
        "memory": {key: raw.get(key) for key in MEMORY_KEYS},
        "capacity": {key: raw.get(key) for key in CAPACITY_KEYS},
        "intrawindow": {
            "rho_gross": float(selected.get("rho_gross", .5)),
            "rho_plus": float(selected.get("rho_plus", .5)),
            "rho_minus": float(selected.get("rho_minus", .5)),
            "treasury_field": None,
            "reference_price_field": price_field,
            "treasury_override_enabled": True,
            "treasury_override": float(selected.get("treasury", 0.0)),
            "position_limit_enabled": False,
            "position_limit_ratio": 25.0,
            "position_limit_field": float_field,
            "topology": "calendar",
        },
        "scenarios": {
            scenario_id: {
                "id": scenario_id,
                "name": "Cenário principal",
                "actions": list(raw.get("actions", [])),
            }
        },
        "active_scenario_id": scenario_id,
        "reference_ticker": raw.get("exp_ticker") or raw.get("iw_ticker"),
        "opening_information": float(raw.get("exp_information", raw.get("iw_opening_information", 0.0)) or 0.0),
    }
    return {
        "id": "experimento_inicial",
        "name": str(raw.get("spec_name") or "Experimento inicial"),
        "status": "draft",
        "created_at": _now(),
        "updated_at": _now(),
        "config": config,
        "history": _history(),
        "last_run": None,
    }


def migrate_legacy(raw: dict[str, Any]) -> dict[str, Any]:
    schema = int(raw.get("project_schema", 0) or 0)
    if schema == PROJECT_SCHEMA:
        foundation_state = raw.setdefault("foundation", {}).setdefault("state", {})
        rows = foundation_state.get("base_table", [])
        numeric = _numeric_columns(rows)
        detected_price = next((name for name in numeric if name.upper() in {"LAST_PRICE", "PRICE", "CURRENT_PRICE", "PRECO_ATUAL"}), None)
        experiments = raw.get("experiments", {})
        semantic_mappings = foundation_state.setdefault("semantic_mappings", {})
        if "treasury" not in semantic_mappings:
            legacy_treasury = next((
                experiment.get("config", {}).get("intrawindow", {}).get("treasury_field")
                for collection in ("drafts", "completed", "archived")
                for experiment in experiments.get(collection, {}).values()
                if experiment.get("config", {}).get("intrawindow", {}).get("treasury_field")
            ), None)
            treasury_aliases = {"TREASURY_SHARES", "TREASURY", "ACOES_TESOURARIA", "AÇÕES_EM_TESOURARIA"}
            semantic_mappings["treasury"] = legacy_treasury or next((name for name in numeric if name.upper() in treasury_aliases), None)
        scenario_owner = raw.setdefault("scenarios", {"items": {}, "active_id": None})
        scenario_owner.setdefault("archived", {})
        if "reference_price" not in semantic_mappings:
            semantic_mappings["reference_price"] = scenario_owner.get("reference_price_field") or next((
                experiment.get("config", {}).get("intrawindow", {}).get("reference_price_field")
                for collection in ("drafts", "completed", "archived")
                for experiment in experiments.get(collection, {}).values()
                if experiment.get("config", {}).get("intrawindow", {}).get("reference_price_field")
            ), None) or detected_price
        scenario_owner.pop("reference_price_field", None)
        for collection in ("drafts", "completed", "archived"):
            for experiment in experiments.get(collection, {}).values():
                iw = experiment.setdefault("config", {}).setdefault("intrawindow", {})
                iw.pop("reference_price_field", None)
        ui = raw.setdefault("ui", {})
        if ui.get("main_nav") == "Experimentos": ui["main_nav"] = "Especificações"
        if ui.get("experiment_section") in {"Avaliar", "Comparar"}: ui["experiment_section"] = "Visão geral"
        _ensure_v39_negative_scenario(raw)
        adopt_global_treasury_mapping(raw)
        return raw
    if schema == 2:
        project = deepcopy(raw)
        rows = project.get("foundation", {}).get("state", {}).get("base_table", [])
        numeric = _numeric_columns(rows)
        detected_price = next((name for name in numeric if name.upper() in {"LAST_PRICE", "PRICE", "CURRENT_PRICE", "PRECO_ATUAL"}), None)
        scenarios: dict[str, dict[str, Any]] = {}
        evaluations: dict[str, dict[str, Any]] = {}
        active_scenario_id = None
        for collection in ("drafts", "completed", "archived"):
            for experiment in project.get("experiments", {}).get(collection, {}).values():
                config = experiment.setdefault("config", {})
                ticker = config.pop("reference_ticker", None) or (experiment.get("last_run") or {}).get("meta", {}).get("ticker") or "PETR4"
                embedded = config.pop("scenarios", {})
                old_active = config.pop("active_scenario_id", None)
                for old_id, scenario in embedded.items():
                    scenario_id = old_id
                    if scenario_id not in scenarios:
                        strategy = str(scenario.get("name") or "Estratégia sem nome")
                        prefix = f"{ticker} · "
                        if strategy.startswith(prefix): strategy = strategy[len(prefix):]
                        scenarios[scenario_id] = {
                            "id": scenario_id, "company": ticker, "strategy": strategy,
                            "description": str(scenario.get("description", "")),
                            "actions": deepcopy(scenario.get("actions", [])),
                            "created_at": experiment.get("created_at", _now()),
                            "updated_at": experiment.get("updated_at", _now()),
                            "history": _history(),
                        }
                    if old_id == old_active and active_scenario_id is None:
                        active_scenario_id = scenario_id
                last_run = experiment.pop("last_run", None)
                if last_run:
                    meta = last_run.get("meta", {})
                    matched = next((sid for sid, scenario in scenarios.items() if scenario["company"] == ticker and scenario["strategy"] == meta.get("scenario")), old_active)
                    evaluation_id = _fingerprint({"experiment": experiment.get("id"), "scenario": matched, "result": last_run})
                    evaluations[evaluation_id] = {
                        "id": evaluation_id, "experiment_id": experiment.get("id"), "scenario_id": matched,
                        "created_at": experiment.get("updated_at", _now()), "result": last_run,
                    }
        project["project_schema"] = PROJECT_SCHEMA
        project["scenarios"] = {"items": scenarios, "active_id": active_scenario_id or next(iter(scenarios), None)}
        project.setdefault("foundation", {}).setdefault("state", {}).setdefault("semantic_mappings", {})["reference_price"] = detected_price
        project["evaluations"] = evaluations
        project.setdefault("ui", {})["main_nav"] = "Cenários" if project.get("ui", {}).get("main_nav") == "Cenários" else project.get("ui", {}).get("main_nav", "Dados")
        return migrate_legacy(project)
    dictionary_keys = {"base_provenance", "semantic_mappings"}
    foundation = {key: deepcopy(raw.get(key, {} if key in dictionary_keys else [])) for key in FOUNDATION_KEYS}
    experiment = _legacy_experiment(raw)
    legacy_project = {
        "project_schema": 2,
        "updated_at": _now(),
        "foundation": {"state": foundation, "history": _history(), "snapshots": {}},
        "experiments": {"drafts": {experiment["id"]: experiment}, "completed": {}, "archived": {}},
        "active_experiment_id": experiment["id"],
        "ui": {"main_nav": "Dados", "experiment_section": "Visão geral"},
    }
    return migrate_legacy(legacy_project)


def load_project(path: Path) -> dict[str, Any]:
    if not path.exists():
        return migrate_legacy({})
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return migrate_legacy({})
        return migrate_legacy(raw)
    except (OSError, json.JSONDecodeError):
        return migrate_legacy({})


def save_project(path: Path, project: dict[str, Any]) -> None:
    project = deepcopy(project)
    project["project_schema"] = PROJECT_SCHEMA
    project["updated_at"] = _now()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(project, ensure_ascii=False, indent=2, sort_keys=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def active_draft(project: dict[str, Any]) -> dict[str, Any] | None:
    experiment_id = project.get("active_experiment_id")
    return project.get("experiments", {}).get("drafts", {}).get(experiment_id)


def flat_view(project: dict[str, Any]) -> dict[str, Any]:
    state = deepcopy(project["foundation"]["state"])
    draft = active_draft(project)
    if draft:
        config = draft["config"]
        state.update(config.get("memory", {}))
        state.update(config.get("capacity", {}))
        iw = config.get("intrawindow", {})
        state.update({
            "configs": {
                draft["name"]: {
                    "h_gross": 0.0, "h_plus": 0.0, "h_minus": 0.0,
                    "rho_gross": iw.get("rho_gross", .5), "rho_plus": iw.get("rho_plus", .5),
                    "rho_minus": iw.get("rho_minus", .5), "treasury": iw.get("treasury_override", 0.0),
                }
            },
            "iw_config": draft["name"], "exp_config": draft["name"],
            "iw_ticker": None, "exp_ticker": None,
            "iw_opening_information": config.get("opening_information", 0.0),
            "exp_information": config.get("opening_information", 0.0),
            "spec_name": draft["name"],
            "active_scenario_id": project.get("scenarios", {}).get("active_id"),
            "treasury_field": state.get("semantic_mappings", {}).get("treasury"),
            "reference_price_field": state.get("semantic_mappings", {}).get("reference_price"),
            "treasury_override_enabled": iw.get("treasury_override_enabled", False),
            "treasury_override_explicit": iw.get("treasury_override_explicit", False),
            "treasury_override": iw.get("treasury_override", 0.0),
            "position_limit_enabled": iw.get("position_limit_enabled", False),
            "position_limit_ratio": iw.get("position_limit_ratio", 25.0),
            "position_limit_field": iw.get("position_limit_field"),
        })
    else:
        state.update({"configs": {}, "spec_name": ""})
    scenario = project.get("scenarios", {}).get("items", {}).get(project.get("scenarios", {}).get("active_id"), {})
    state["active_scenario_id"] = project.get("scenarios", {}).get("active_id")
    state["actions"] = deepcopy(scenario.get("actions", []))
    state["main_nav"] = project.get("ui", {}).get("main_nav", "Dados")
    return state


def _push(history: dict[str, Any], state: dict[str, Any]) -> None:
    history.setdefault("undo", []).append(deepcopy(state))
    history["undo"] = history["undo"][-HISTORY_LIMIT:]
    history["redo"] = []


def commit_foundation(project: dict[str, Any], state: dict[str, Any]) -> bool:
    target = project["foundation"]
    if target.get("state") == state:
        return False
    _push(target.setdefault("history", _history()), target.get("state", {}))
    target["state"] = deepcopy(state)
    return True


def commit_active_experiment(project: dict[str, Any], name: str, config: dict[str, Any]) -> bool:
    draft = active_draft(project)
    if not draft:
        return False
    semantic = {"name": name, "config": config}
    previous = {"name": draft.get("name"), "config": draft.get("config")}
    changed = semantic != previous
    if changed:
        _push(draft.setdefault("history", _history()), previous)
        draft["name"] = name
        draft["config"] = deepcopy(config)
        draft["updated_at"] = _now()
    return changed


def active_scenario(project: dict[str, Any]) -> dict[str, Any] | None:
    owner = project.get("scenarios", {})
    return owner.get("items", {}).get(owner.get("active_id"))


def commit_active_scenario(project: dict[str, Any], company: str, strategy: str, description: str, actions: list[dict[str, Any]]) -> bool:
    scenario = active_scenario(project)
    if not scenario:
        return False
    current = {key: deepcopy(scenario.get(key)) for key in ("company", "strategy", "description", "actions")}
    target = {"company": company, "strategy": strategy, "description": description, "actions": deepcopy(actions)}
    if current == target:
        return False
    _push(scenario.setdefault("history", _history()), current)
    scenario.update(target)
    scenario["updated_at"] = _now()
    return True


def create_scenario(project: dict[str, Any], company: str, strategy: str, source: dict[str, Any] | None = None) -> str:
    scenario_id = "cenario_" + uuid4().hex[:10]
    project.setdefault("scenarios", {}).setdefault("items", {})[scenario_id] = {
        "id": scenario_id, "company": company, "strategy": strategy,
        "description": str(source.get("description", "")) if source else "",
        "actions": deepcopy(source.get("actions", [])) if source else [],
        "created_at": _now(), "updated_at": _now(), "history": _history(),
        "derived_from": source.get("id") if source else None,
    }
    project["scenarios"]["active_id"] = scenario_id
    return scenario_id


def delete_scenario(project: dict[str, Any], scenario_id: str) -> bool:
    """Archive a scenario so an accidental removal is recoverable."""
    items = project.get("scenarios", {}).get("items", {})
    if scenario_id not in items:
        return False
    item = items.pop(scenario_id)
    item["archived_at"] = _now()
    project["scenarios"].setdefault("archived", {})[scenario_id] = item
    project["scenarios"]["active_id"] = next(iter(items), None)
    return True


def restore_scenario(project: dict[str, Any], scenario_id: str) -> bool:
    owner = project.get("scenarios", {})
    archived = owner.setdefault("archived", {})
    if scenario_id not in archived:
        return False
    item = archived.pop(scenario_id)
    item.pop("archived_at", None)
    item["updated_at"] = _now()
    owner.setdefault("items", {})[scenario_id] = item
    owner["active_id"] = scenario_id
    return True


def history_status(project: dict[str, Any], scope: str) -> tuple[int, int]:
    if scope == "foundation":
        history = project["foundation"].setdefault("history", _history())
    elif scope == "scenario":
        scenario = active_scenario(project)
        history = scenario.setdefault("history", _history()) if scenario else _history()
    else:
        draft = active_draft(project)
        history = draft.setdefault("history", _history()) if draft else _history()
    return len(history.get("undo", [])), len(history.get("redo", []))


def undo(project: dict[str, Any], scope: str) -> bool:
    if scope == "foundation":
        owner = project["foundation"]; current = deepcopy(owner.get("state", {}))
        apply = lambda value: owner.__setitem__("state", value)
    elif scope == "scenario":
        owner = active_scenario(project)
        if not owner: return False
        current = {key: deepcopy(owner.get(key)) for key in ("company", "strategy", "description", "actions")}
        def apply(value): owner.update(value)
    else:
        owner = active_draft(project)
        if not owner: return False
        current = {"name": owner.get("name"), "config": deepcopy(owner.get("config"))}
        def apply(value):
            owner["name"] = value["name"]; owner["config"] = value["config"]
    history = owner.setdefault("history", _history())
    if not history.get("undo"): return False
    target = history["undo"].pop()
    history.setdefault("redo", []).append(current)
    history["redo"] = history["redo"][-HISTORY_LIMIT:]
    apply(target)
    return True


def redo(project: dict[str, Any], scope: str) -> bool:
    if scope == "foundation":
        owner = project["foundation"]; current = deepcopy(owner.get("state", {}))
        apply = lambda value: owner.__setitem__("state", value)
    elif scope == "scenario":
        owner = active_scenario(project)
        if not owner: return False
        current = {key: deepcopy(owner.get(key)) for key in ("company", "strategy", "description", "actions")}
        def apply(value): owner.update(value)
    else:
        owner = active_draft(project)
        if not owner: return False
        current = {"name": owner.get("name"), "config": deepcopy(owner.get("config"))}
        def apply(value):
            owner["name"] = value["name"]; owner["config"] = value["config"]
    history = owner.setdefault("history", _history())
    if not history.get("redo"): return False
    target = history["redo"].pop()
    history.setdefault("undo", []).append(current)
    history["undo"] = history["undo"][-HISTORY_LIMIT:]
    apply(target)
    return True


def create_draft(project: dict[str, Any], name: str, source: dict[str, Any] | None = None) -> str:
    experiment_id = "exp_" + uuid4().hex[:10]
    if source:
        config = deepcopy(source["config"])
    else:
        config = _legacy_experiment({})["config"]
    project["experiments"]["drafts"][experiment_id] = {
        "id": experiment_id, "name": name, "status": "draft", "created_at": _now(),
        "updated_at": _now(), "config": config, "history": _history(),
        "derived_from": source.get("id") if source else None,
    }
    project["active_experiment_id"] = experiment_id
    return experiment_id


def duplicate_as_draft(project: dict[str, Any], source: dict[str, Any]) -> str:
    return create_draft(project, f'{source.get("name", "Experimento")} · cópia', source)


def reopen_completed(project: dict[str, Any], experiment_id: str) -> bool:
    """Reopen a completed specification in place, preserving its identity."""
    completed = project.get("experiments", {}).get("completed", {})
    source = completed.get(experiment_id)
    if not source:
        return False
    draft = deepcopy(source)
    draft["status"] = "draft"
    draft["updated_at"] = _now()
    draft["history"] = _history()
    draft["reopened_from_fingerprint"] = draft.pop("fingerprint", None)
    draft.pop("completed_at", None)
    draft.pop("engine_version", None)
    completed.pop(experiment_id)
    project["experiments"]["drafts"][experiment_id] = draft
    project["active_experiment_id"] = experiment_id
    if project.get("ui", {}).get("view_completed_id") == experiment_id:
        project["ui"].pop("view_completed_id", None)
    return True


def finalize_active(project: dict[str, Any]) -> str | None:
    draft = active_draft(project)
    if not draft: return None
    completed = deepcopy(draft)
    completed["status"] = "completed"
    completed["completed_at"] = _now()
    completed["engine_version"] = ENGINE_VERSION
    completed["fingerprint"] = _fingerprint({"name": completed["name"], "config": completed["config"]})
    completed.pop("history", None)
    completed.pop("reopened_from_fingerprint", None)
    experiment_id = completed["id"]
    project["experiments"]["completed"][experiment_id] = completed
    project["experiments"]["drafts"].pop(experiment_id, None)
    project["active_experiment_id"] = None
    return experiment_id


def delete_experiment(project: dict[str, Any], experiment_id: str) -> bool:
    for bucket in ("drafts", "completed"):
        if experiment_id in project["experiments"][bucket]:
            item = project["experiments"][bucket].pop(experiment_id)
            item["archived_at"] = _now()
            project["experiments"]["archived"][experiment_id] = item
            if project.get("active_experiment_id") == experiment_id:
                project["active_experiment_id"] = None
            return True
    return False


def foundation_snapshot(project: dict[str, Any], label: str | None = None) -> str:
    state = deepcopy(project["foundation"]["state"])
    snapshot_id = _fingerprint(state)
    project["foundation"].setdefault("snapshots", {})[snapshot_id] = {
        "id": snapshot_id, "label": label or f"Base {snapshot_id}", "created_at": _now(), "state": state,
    }
    return snapshot_id
