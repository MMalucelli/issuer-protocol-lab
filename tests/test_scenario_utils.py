from issuer_lab.scenario_utils import apply_editor_delta, comparison_projection, editor_records_to_actions, executable_actions, available_comparison_pairs, semantic_field_options


def test_incomplete_editor_rows_are_preserved_but_not_executed():
    draft = editor_records_to_actions([
        {"Operação": "Compra", "Quantidade": 0, "Preço": 38.5, "Momento": "10:00", "Observação": "preenchendo"},
        {"Operação": "Venda", "Quantidade": 100, "Preço": 38.5, "Momento": "11:00", "Observação": "válida"},
    ])
    assert len(draft) == 2
    assert draft[0]["quantity"] == 0
    assert executable_actions(draft) == [draft[1]]


def test_invalid_numeric_values_become_safe_incomplete_rows():
    draft = editor_records_to_actions([{"Operação": "Compra", "Quantidade": "", "Preço": float("nan")}])
    assert draft[0]["quantity"] == 0
    assert draft[0]["price"] == 0
    assert executable_actions(draft) == []


def test_editor_delta_commits_a_cell_edit_on_the_first_event():
    actions = editor_records_to_actions([
        {"Operação": "Compra", "Quantidade": 100, "Preço": 38.5, "Momento": "10:00"},
    ])
    updated = apply_editor_delta(actions, {"edited_rows": {0: {"Quantidade": 250}}})
    assert updated[0]["quantity"] == 250
    assert updated[0]["price"] == 38.5


def test_editor_delta_handles_string_indexes_additions_and_deletions():
    actions = editor_records_to_actions([
        {"Operação": "Compra", "Quantidade": 100, "Preço": 10},
        {"Operação": "Venda", "Quantidade": 50, "Preço": 11},
    ])
    updated = apply_editor_delta(actions, {
        "edited_rows": {"1": {"Quantidade": 75}},
        "deleted_rows": [0],
        "added_rows": [{"Operação": "Compra", "Quantidade": 20, "Preço": 12}],
    })
    assert [(row["side"], row["quantity"], row["price"]) for row in updated] == [
        ("SELL", 75, 11),
        ("BUY", 20, 12),
    ]


def test_fixed_scenario_comparison_preserves_absolute_share_domain():
    projected = comparison_projection(4_400_000, 8_250_000, .70, normalized=False)
    assert projected["value"] == 4_400_000
    assert projected["h_axis"] == 8_250_000
    assert projected["q_axis"] == 5_775_000
    assert projected["q_ratio"] == .70


def test_fixed_specification_comparison_normalizes_scenario_domain():
    projected = comparison_projection(4_400_000, 8_250_000, .70, normalized=True)
    assert projected["value"] == projected["utilization"]
    assert projected["h_axis"] == 1.0
    assert projected["q_axis"] == .70
    assert projected["q_absolute"] == 5_775_000


def test_comparison_graph_ignores_pairs_without_successful_evaluation():
    good=("spec_ok","scenario")
    failed=("spec_invalid","scenario")
    assert available_comparison_pairs([good,failed],{good:(object(),object())}) == [good]


def test_saved_semantic_fields_survive_temporarily_empty_numeric_options():
    assert semantic_field_options([],"TREASURY_SHARES","TOTAL_SHARES") == [None,"TREASURY_SHARES","TOTAL_SHARES"]
    assert semantic_field_options(["TREASURY_SHARES"],"TREASURY_SHARES") == [None,"TREASURY_SHARES"]
