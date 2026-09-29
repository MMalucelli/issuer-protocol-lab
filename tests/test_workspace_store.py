from __future__ import annotations

import json
from pathlib import Path

from issuer_lab.workspace_store import (
    WORKSPACE_VERSION,
    history_status,
    load_workspace,
    redo_workspace,
    save_workspace,
    undo_workspace,
)
from issuer_lab.project_store import load_project


def test_workspace_roundtrip_is_versioned(tmp_path):
    target = tmp_path / ".issuer_lab" / "workspace.json"
    payload = {"base_table": [{"main_id": "PETR4"}], "GAIN": 0.42}

    save_workspace(target, payload)

    loaded = load_workspace(target)
    assert loaded["workspace_version"] == WORKSPACE_VERSION
    assert loaded["base_table"] == [{"main_id": "PETR4"}]
    assert loaded["GAIN"] == 0.42
    assert not list(target.parent.glob("*.tmp"))


def test_invalid_workspace_is_ignored(tmp_path):
    target = tmp_path / "workspace.json"
    target.write_text("{incomplete", encoding="utf-8")

    assert load_workspace(target) == {}


def test_non_object_workspace_is_ignored(tmp_path):
    target = tmp_path / "workspace.json"
    target.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    assert load_workspace(target) == {}


def test_project_canonical_state_is_present_and_complete():
    target = Path(__file__).resolve().parents[1] / "lab_state.json"
    loaded = load_project(target)

    assert loaded["project_schema"] == 3
    assert loaded["foundation"]["state"]["base_table"]
    assert loaded["foundation"]["state"]["base_provenance"]
    experiments = {**loaded["experiments"]["completed"], **loaded["experiments"]["drafts"]}
    experiment = next(iter(experiments.values()))
    assert experiment["config"]["capacity"]["h0_gross_expr"]
    assert experiment["config"]["capacity"]["hmax_expr"]
    assert "scenarios" not in experiment["config"]
    assert loaded["scenarios"]["items"]


def test_undo_and_redo_restore_complete_semantic_state(tmp_path):
    target = tmp_path / "lab_state.json"
    first = {"base_table": [{"main_id": "PETR4"}], "derived_defs": [], "main_nav": "Dados"}
    second = {"base_table": [{"main_id": "PETR4"}], "derived_defs": [{"Nome": "X"}], "main_nav": "Variáveis"}

    save_workspace(target, first)
    save_workspace(target, second)
    assert history_status(target) == (1, 0)

    restored = undo_workspace(target)
    assert restored["derived_defs"] == []
    assert restored["main_nav"] == "Variáveis"  # navigation is not undone
    assert history_status(target) == (0, 1)

    restored = redo_workspace(target)
    assert restored["derived_defs"] == [{"Nome": "X"}]
    assert history_status(target) == (1, 0)


def test_navigation_changes_do_not_pollute_history(tmp_path):
    target = tmp_path / "lab_state.json"
    save_workspace(target, {"base_table": [{"main_id": "PETR4"}], "main_nav": "Dados"})
    save_workspace(target, {"base_table": [{"main_id": "PETR4"}], "main_nav": "Auditoria"})

    assert history_status(target) == (0, 0)
    assert load_workspace(target)["main_nav"] == "Auditoria"


def test_new_change_after_undo_clears_redo_branch(tmp_path):
    target = tmp_path / "lab_state.json"
    save_workspace(target, {"base_table": [{"main_id": "A"}]})
    save_workspace(target, {"base_table": [{"main_id": "B"}]})
    undo_workspace(target)
    assert history_status(target) == (0, 1)

    save_workspace(target, {"base_table": [{"main_id": "C"}]})
    assert history_status(target) == (1, 0)
