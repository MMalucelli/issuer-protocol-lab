from pathlib import Path

from copy import deepcopy

from issuer_lab.project_store import load_project, migrate_legacy


ROOT = Path(__file__).resolve().parents[1]


def test_shipped_review_state_exercises_experiment_workspace():
    project = load_project(ROOT / "lab_state.json")
    experiments = project["experiments"]
    assert len(experiments["drafts"]) == 0
    assert len(experiments["completed"]) == 8
    assert project["active_experiment_id"] is None
    for item in [*experiments["drafts"].values(), *experiments["completed"].values()]:
        assert "scenarios" not in item["config"]
        assert "reference_ticker" not in item["config"]
        assert "last_run" not in item
    assert len(project["scenarios"]["items"]) == 13
    assert project["foundation"]["state"]["semantic_mappings"]["reference_price"] == "LAST_PRICE"
    assert "reference_price_field" not in project["scenarios"]
    assert {item["company"] for item in project["scenarios"]["items"].values()} == {"PETR4", "MGLU3", "VALE3", "KEPL3"}
    assert all("reference_price_field" not in item["config"]["intrawindow"] for item in [*experiments["drafts"].values(), *experiments["completed"].values()])


def test_scenarios_have_company_and_exogenous_strategy_names():
    project = load_project(ROOT / "lab_state.json")
    scenarios = project["scenarios"]["items"]
    assert scenarios["cruza_q_e_retorna"]["strategy"] == "Acumulação com redução no fechamento"
    negative = scenarios["pet4_venda_liquida_limite"]
    assert negative["company"] == "PETR4"
    assert [action["side"] for action in negative["actions"]] == ["SELL", "SELL"]
    assert sum(action["quantity"] for action in negative["actions"]) == 110_000
    assert all("Q" not in scenario["strategy"] for scenario in scenarios.values())


def test_v39_negative_scenario_migrates_existing_review_state_once():
    project = load_project(ROOT / "lab_state.json")
    project.pop("migrations", None)
    project["scenarios"]["items"].pop("pet4_venda_liquida_limite", None)
    migrated = migrate_legacy(deepcopy(project))
    scenario = migrated["scenarios"]["items"]["pet4_venda_liquida_limite"]
    assert scenario["actions"][0]["side"] == "SELL"
    scenario["strategy"] = "Nome editado pelo usuário"
    assert migrate_legacy(migrated)["scenarios"]["items"]["pet4_venda_liquida_limite"]["strategy"] == "Nome editado pelo usuário"
