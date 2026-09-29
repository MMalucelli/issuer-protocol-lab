from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from issuer_lab.project_store import ENGINE_VERSION, load_project, save_project


def fingerprint(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def revise(source: Path, target: Path) -> None:
    project = load_project(source)
    now = datetime.now(timezone.utc).isoformat()

    # Canonical semantic mappings belong only to the analytical foundation.
    mappings = project["foundation"]["state"].setdefault("semantic_mappings", {})
    mappings["treasury"] = "TREASURY_SHARES"
    mappings["reference_price"] = "LAST_PRICE"
    project["foundation"]["history"] = {"undo": [], "redo": []}
    project["foundation"]["snapshots"] = {}

    # Restore the useful closing-reduction example and remove the accidental
    # duplicate/corrupted scenario records.
    scenarios = project["scenarios"].setdefault("items", {})
    scenarios.pop("cenario_db64d9ec40", None)
    scenarios["cruza_q_e_retorna"] = {
        "id": "cruza_q_e_retorna",
        "company": "PETR4",
        "strategy": "Acumulação com redução no fechamento",
        "description": "Acumulação seguida de redução relevante perto do fechamento; cruza Q intraday e pode retornar abaixo dele.",
        "actions": [
            {"side": "BUY", "quantity": 5_200_000.0, "price": 38.5, "time": "10:20", "note": "Ultrapassa Q net+ intraday"},
            {"side": "SELL", "quantity": 1_000_000.0, "price": 38.5, "time": "15:45", "note": "Reduz a posição antes do fechamento"},
        ],
        "created_at": now,
        "updated_at": now,
        "derived_from": None,
        "history": {"undo": [], "redo": []},
    }

    # A 3.6-million sell trajectory separates the specifications instead of
    # forcing every one of them to finish mechanically at 100% of H net−.
    negative = scenarios["pet4_venda_liquida_limite"]
    negative.update({
        "company": "PETR4",
        "strategy": "Venda líquida discriminante",
        "description": "Duas vendas que separam capacidades, limiares Q e preenchimentos parciais entre as especificações.",
        "actions": [
            {"side": "SELL", "quantity": 1_800_000.0, "price": 38.5, "time": "10:30", "note": "Primeira perna de venda líquida"},
            {"side": "SELL", "quantity": 1_800_000.0, "price": 38.5, "time": "15:30", "note": "Testa Q e H net− na segunda perna"},
        ],
        "updated_at": now,
        "history": {"undo": [], "redo": []},
    })
    for scenario in scenarios.values():
        scenario["history"] = {"undo": [], "redo": []}
    project["scenarios"]["archived"] = {}
    project["scenarios"]["active_id"] = "pet4_venda_liquida_limite"

    # Normalize all specifications, eliminate disabled legacy override residue,
    # and freeze the complete eight-specification baseline again.
    experiments = project["experiments"]
    all_specs = {**experiments.get("completed", {}), **experiments.get("drafts", {})}
    completed = {}
    for experiment_id, source_experiment in all_specs.items():
        experiment = deepcopy(source_experiment)
        # Keep inherited information small enough for a readable comparison.
        # Both cases use the same I so their difference isolates the response
        # curve: hyperbolic (responsive memory) versus linear saturation.
        if experiment_id in {"experimento_memoria_responsiva", "experimento_saturacao_linear"}:
            experiment["config"]["opening_information"] = 0.05
        iw = experiment["config"]["intrawindow"]
        iw.pop("treasury_field", None)
        iw["treasury_override_enabled"] = False
        iw["treasury_override_explicit"] = False
        iw["treasury_override"] = 0.0
        experiment["status"] = "completed"
        experiment["updated_at"] = now
        experiment["completed_at"] = now
        experiment["engine_version"] = ENGINE_VERSION
        experiment["fingerprint"] = fingerprint({"name": experiment["name"], "config": experiment["config"]})
        for stale_key in ("history", "reopened_from_fingerprint", "archived_at"):
            experiment.pop(stale_key, None)
        completed[experiment_id] = experiment
    experiments["completed"] = completed
    experiments["drafts"] = {}
    experiments["archived"] = {}
    project["active_experiment_id"] = None

    # Cached evaluations refer to the former scenario/configuration revisions.
    project["evaluations"] = {}
    ui = project.setdefault("ui", {})
    ui.update({
        "main_nav": "Comparar",
        "comparison_mode": "Especificações × um cenário",
        "comparison_fixed_scenario_id": "pet4_venda_liquida_limite",
        "specification_preview_scenario_id": "pet4_venda_liquida_limite",
    })
    ui["comparison_selected_experiment_ids"] = [
        experiment_id for experiment_id in (
            "experimento_capacidade_conservadora",
            "experimento_capacidade_expansiva",
            "experimento_capacidade_fixa",
            "experimento_memoria_responsiva",
            "experimento_q_antecipado",
            "experimento_q_assimetrico",
            "experimento_saturacao_linear",
            "exp_2fc419095e",
        ) if experiment_id in completed
    ]
    selected_scenarios = [scenario_id for scenario_id in ui.get("comparison_selected_scenario_ids", []) if scenario_id in scenarios]
    if "cruza_q_e_retorna" not in selected_scenarios:
        selected_scenarios.insert(1, "cruza_q_e_retorna")
    ui["comparison_selected_scenario_ids"] = selected_scenarios
    ui.pop("view_completed_id", None)

    save_project(target, project)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize the final Issuer Protocol Lab review state.")
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    revise(args.source, args.target)


if __name__ == "__main__":
    main()
