from issuer_lab.project_store import (
    HISTORY_LIMIT, active_scenario, commit_active_experiment, commit_active_scenario, commit_foundation, create_draft,
    delete_scenario, finalize_active, flat_view, history_status, load_project, migrate_legacy, redo, reopen_completed, restore_scenario, save_project, undo,
)


def legacy_state():
    return {
        "base_table": [{"main_id": "PETR4", "FLOAT_SHARES": 1000, "LAST_PRICE": 31.25}],
        "base_provenance": {}, "derived_defs": [], "source_specs": [],
        "configs": {"Baseline": {"h_gross": 100, "h_plus": 80, "h_minus": 60, "rho_gross": .5, "rho_plus": .5, "rho_minus": .5, "treasury": 20}},
        "actions": [{"side": "BUY", "quantity": 10, "price": 1}],
        "h0_gross_expr": "FLOAT_SHARES * .1", "h0_plus_expr": "FLOAT_SHARES * .08",
        "h0_minus_expr": "FLOAT_SHARES * .06", "hmax_expr": "H0 * 5",
        "signal_expr": "I", "update_expr": "I + U", "decay_expr": "I",
        "I_MULT": 1, "GAIN": .3, "LAMBDA": .1, "ACCEL": .1, "REV_PENALTY": .2,
        "sat_kind": "linear", "sat_shape": 1,
    }


def test_legacy_state_migrates_without_losing_base_or_scenario():
    project = migrate_legacy(legacy_state())
    view = flat_view(project)
    assert len(view["base_table"]) == 1
    assert view["actions"][0]["side"] == "BUY"
    assert view["treasury_override_enabled"] is True
    assert view["position_limit_field"] == "FLOAT_SHARES"
    assert view["reference_price_field"] == "LAST_PRICE"
    assert project["project_schema"] == 3
    assert len(project["scenarios"]["items"]) == 1
    assert "scenarios" not in next(iter(project["experiments"]["drafts"].values()))["config"]


def test_current_state_gains_detected_global_reference_price_without_losing_data():
    project = migrate_legacy(legacy_state())
    project["foundation"]["state"]["semantic_mappings"].pop("reference_price", None)
    project["scenarios"]["reference_price_field"] = "LAST_PRICE"
    upgraded = migrate_legacy(project)
    assert upgraded is project
    assert project["foundation"]["state"]["semantic_mappings"]["reference_price"] == "LAST_PRICE"
    assert "reference_price_field" not in project["scenarios"]


def test_existing_treasury_mapping_moves_from_specification_to_foundation():
    project = migrate_legacy(legacy_state())
    project["foundation"]["state"].pop("semantic_mappings", None)
    draft = next(iter(project["experiments"]["drafts"].values()))
    draft["config"]["intrawindow"]["treasury_field"] = "TREASURY_SHARES"
    migrate_legacy(project)
    assert project["foundation"]["state"]["semantic_mappings"]["treasury"] == "TREASURY_SHARES"
    assert flat_view(project)["treasury_field"] == "TREASURY_SHARES"


def test_global_treasury_mapping_retires_legacy_default_override():
    state = legacy_state()
    state["base_table"][0]["TREASURY_SHARES"] = 125_000
    project = migrate_legacy(state)
    draft = next(iter(project["experiments"]["drafts"].values()))
    iw = draft["config"]["intrawindow"]
    assert project["foundation"]["state"]["semantic_mappings"]["treasury"] == "TREASURY_SHARES"
    assert iw["treasury_override_enabled"] is False


def test_explicit_treasury_override_survives_global_mapping_migration():
    project = migrate_legacy(legacy_state())
    project["foundation"]["state"]["base_table"][0]["TREASURY_SHARES"] = 125_000
    project["foundation"]["state"]["semantic_mappings"] = {"treasury": "TREASURY_SHARES"}
    project["migrations"].pop("v42_global_treasury_override_cleanup", None)
    draft = next(iter(project["experiments"]["drafts"].values()))
    iw = draft["config"]["intrawindow"]
    iw["treasury_override_enabled"] = True
    iw["treasury_override_explicit"] = True
    migrate_legacy(project)
    assert iw["treasury_override_enabled"] is True


def test_explicitly_empty_semantic_mappings_are_not_guessed_again():
    project = migrate_legacy(legacy_state())
    mappings = project["foundation"]["state"]["semantic_mappings"]
    mappings["treasury"] = None
    mappings["reference_price"] = None
    project["foundation"]["state"]["base_table"][0].update({"TREASURY_SHARES": 125_000, "LAST_PRICE": 31.25})
    migrate_legacy(project)
    assert mappings == {"treasury": None, "reference_price": None}


def test_semantic_mappings_survive_file_roundtrip_exactly(tmp_path):
    project = migrate_legacy(legacy_state())
    project["foundation"]["state"]["semantic_mappings"] = {
        "treasury": "CUSTOM_TREASURY",
        "reference_price": None,
    }
    path = tmp_path / "lab_state.json"
    save_project(path, project)
    loaded = load_project(path)
    assert loaded["foundation"]["state"]["semantic_mappings"] == {
        "treasury": "CUSTOM_TREASURY",
        "reference_price": None,
    }


def test_current_state_migrates_old_navigation_to_specifications():
    project = migrate_legacy(legacy_state())
    project["ui"] = {"main_nav": "Experimentos", "experiment_section": "Avaliar"}
    migrate_legacy(project)
    assert project["ui"] == {"main_nav": "Especificações", "experiment_section": "Visão geral"}


def test_foundation_and_experiment_histories_are_independent():
    project = migrate_legacy(legacy_state())
    foundation = project["foundation"]["state"] | {"derived_defs": [{"Nome": "X"}]}
    commit_foundation(project, foundation)
    draft = next(iter(project["experiments"]["drafts"].values()))
    config = draft["config"] | {"opening_information": .4}
    commit_active_experiment(project, draft["name"], config)
    assert history_status(project, "foundation") == (1, 0)
    assert history_status(project, "experiment") == (1, 0)
    undo(project, "experiment")
    assert history_status(project, "foundation") == (1, 0)
    assert history_status(project, "experiment") == (0, 1)
    redo(project, "experiment")
    assert project["foundation"]["state"]["derived_defs"] == [{"Nome": "X"}]


def test_scenario_history_is_independent_from_foundation_and_experiment():
    project = migrate_legacy(legacy_state())
    scenario = active_scenario(project)
    commit_active_scenario(project, "PETR4", "Compra moderada", "Teste", scenario["actions"])
    assert history_status(project, "scenario") == (1, 0)
    assert history_status(project, "foundation") == (0, 0)
    assert history_status(project, "experiment") == (0, 0)
    undo(project, "scenario")
    assert active_scenario(project)["strategy"] == "Cenário principal"


def test_scenario_archive_is_recoverable():
    project = migrate_legacy(legacy_state())
    scenario_id = project["scenarios"]["active_id"]
    original = active_scenario(project).copy()
    assert delete_scenario(project, scenario_id)
    assert scenario_id not in project["scenarios"]["items"]
    assert project["scenarios"]["archived"][scenario_id]["strategy"] == original["strategy"]
    assert restore_scenario(project, scenario_id)
    assert project["scenarios"]["active_id"] == scenario_id
    assert active_scenario(project)["strategy"] == original["strategy"]


def test_history_is_limited_to_twenty_revisions():
    project = migrate_legacy(legacy_state())
    for index in range(HISTORY_LIMIT + 7):
        state = dict(project["foundation"]["state"])
        state["derived_defs"] = [{"Nome": str(index)}]
        commit_foundation(project, state)
    assert history_status(project, "foundation")[0] == HISTORY_LIMIT


def test_completed_experiment_is_immutable_and_can_seed_new_draft():
    project = migrate_legacy(legacy_state())
    completed_id = finalize_active(project)
    completed = project["experiments"]["completed"][completed_id]
    new_id = create_draft(project, "Nova hipótese", completed)
    assert project["experiments"]["drafts"][new_id]["config"] == completed["config"]
    assert project["experiments"]["drafts"][new_id]["history"] == {"undo": [], "redo": []}


def test_completed_experiment_can_be_reopened_and_finalized_in_place():
    project = migrate_legacy(legacy_state())
    completed_id = finalize_active(project)
    original = project["experiments"]["completed"][completed_id]
    original_fingerprint = original["fingerprint"]
    assert reopen_completed(project, completed_id)
    draft = project["experiments"]["drafts"][completed_id]
    assert project["active_experiment_id"] == completed_id
    assert completed_id not in project["experiments"]["completed"]
    assert draft["config"] == original["config"]
    assert draft["reopened_from_fingerprint"] == original_fingerprint
    draft["name"] = "Especificação corrigida"
    assert finalize_active(project) == completed_id
    corrected = project["experiments"]["completed"][completed_id]
    assert corrected["name"] == "Especificação corrigida"
    assert "reopened_from_fingerprint" not in corrected
