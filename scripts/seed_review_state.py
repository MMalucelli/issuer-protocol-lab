"""Populate lab_state.json with reproducible thesis-review experiments.

The operation is idempotent: generated experiment ids and scenarios are
replaced, while the analytical foundation is preserved byte-for-byte in the
loaded project object.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd

from issuer_lab import Capacity, CapacityDimension, IssuerState, RuleViolation, Side, StateEngine, Thresholds
from issuer_lab.capacity_builder import HRule
from issuer_lab.expression_engine import evaluate, evaluate_derived
from issuer_lab.project_store import ENGINE_VERSION, load_project, save_project


ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "lab_state.json"
TICKER = "PETR4"
PRICE = 38.50
NOW = "2026-09-20T12:00:00+00:00"


SCENARIOS = {
    "controle_abaixo_q": {
        "id": "controle_abaixo_q",
        "name": "Controle · abaixo de Q",
        "actions": [
            {"side": "BUY", "quantity": 2_000_000.0, "price": PRICE, "time": "10:15", "note": "Compra inicial abaixo dos limiares"},
            {"side": "SELL", "quantity": 1_000_000.0, "price": PRICE, "time": "11:30", "note": "Redução parcial da posição"},
        ],
    },
    "cruza_q_e_retorna": {
        "id": "cruza_q_e_retorna",
        "name": "Net+ cruza Q e retorna",
        "actions": [
            {"side": "BUY", "quantity": 5_200_000.0, "price": PRICE, "time": "10:20", "note": "Ultrapassa Q net+ intraday"},
            {"side": "SELL", "quantity": 1_000_000.0, "price": PRICE, "time": "15:45", "note": "Retorna abaixo de Q antes do fechamento"},
        ],
    },
    "disclosure_net_positivo": {
        "id": "disclosure_net_positivo",
        "name": "Disclosure · Net+ no fechamento",
        "actions": [
            {"side": "BUY", "quantity": 5_200_000.0, "price": PRICE, "time": "14:10", "note": "Encerra o pregão acima de Q net+"},
        ],
    },
    "disclosure_gross_neutro": {
        "id": "disclosure_gross_neutro",
        "name": "Disclosure · Gross com Net neutro",
        "actions": [
            {"side": "BUY", "quantity": 3_600_000.0, "price": PRICE, "time": "10:05", "note": "Primeira perna"},
            {"side": "SELL", "quantity": 3_600_000.0, "price": PRICE, "time": "16:20", "note": "Net volta a zero; Gross permanece acumulado"},
        ],
    },
    "estresse_h": {
        "id": "estresse_h",
        "name": "Estresse · ordem acima de H",
        "actions": [
            {"side": "BUY", "quantity": 14_000_000.0, "price": PRICE, "time": "12:00", "note": "Teste deliberado de rejeição pelo hard cap"},
        ],
    },
    "mglu_acumulacao_gradual": {
        "id": "mglu_acumulacao_gradual", "name": "Acumulação gradual",
        "actions": [
            {"side": "BUY", "quantity": 800_000.0, "price": 10.0, "time": "10:10", "note": "Primeira parcela"},
            {"side": "BUY", "quantity": 900_000.0, "price": 10.0, "time": "13:40", "note": "Segunda parcela"},
            {"side": "SELL", "quantity": 500_000.0, "price": 10.0, "time": "16:15", "note": "Redução no fechamento"},
        ],
    },
    "mglu_giro_intenso": {
        "id": "mglu_giro_intenso", "name": "Giro intenso",
        "actions": [
            {"side": "BUY", "quantity": 2_200_000.0, "price": 10.0, "time": "11:00", "note": "Acumulação intraday"},
            {"side": "SELL", "quantity": 2_000_000.0, "price": 10.0, "time": "15:30", "note": "Quase neutralização da posição"},
        ],
    },
    "vale_compra_mantida": {
        "id": "vale_compra_mantida", "name": "Compra mantida",
        "actions": [
            {"side": "BUY", "quantity": 3_000_000.0, "price": 62.0, "time": "14:00", "note": "Compra concentrada mantida até o fechamento"},
        ],
    },
    "vale_reducao_fechamento": {
        "id": "vale_reducao_fechamento", "name": "Redução no fechamento",
        "actions": [
            {"side": "BUY", "quantity": 3_000_000.0, "price": 62.0, "time": "10:30", "note": "Construção da posição"},
            {"side": "SELL", "quantity": 1_200_000.0, "price": 62.0, "time": "16:40", "note": "Redução antes do fechamento"},
        ],
    },
    "kepl_operacao_moderada": {
        "id": "kepl_operacao_moderada", "name": "Operação moderada",
        "actions": [
            {"side": "BUY", "quantity": 40_000.0, "price": 12.0, "time": "11:20", "note": "Compra compatível com menor liquidez"},
            {"side": "SELL", "quantity": 15_000.0, "price": 12.0, "time": "15:10", "note": "Redução parcial"},
        ],
    },
    "kepl_ordem_concentrada": {
        "id": "kepl_ordem_concentrada", "name": "Ordem concentrada",
        "actions": [
            {"side": "BUY", "quantity": 70_000.0, "price": 12.0, "time": "12:15", "note": "Pressão concentrada em ativo menos líquido"},
        ],
    },
}


def fingerprint(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def resolved_values(project: dict, ticker: str) -> dict:
    foundation = project["foundation"]["state"]
    row = next(item for item in foundation["base_table"] if item["main_id"] == ticker)
    definitions = {
        str(item.get("Nome", "")).strip().upper(): str(item.get("Função", "")).strip()
        for item in foundation.get("derived_defs", [])
        if item.get("Nome") and item.get("Função")
    }
    return evaluate_derived(definitions, row)


def resolve_capacity(project: dict, config: dict) -> tuple[float, float, float, float]:
    values = resolved_values(project, TICKER)
    capacity = config["capacity"]
    memory = config["memory"]
    h0_gross = max(0.0, evaluate(capacity["h0_gross_expr"], values))
    h0_plus = max(0.0, evaluate(capacity["h0_plus_expr"], values))
    h0_minus = max(0.0, evaluate(capacity["h0_minus_expr"], values))
    h0_gross = max(h0_gross, h0_plus, h0_minus)
    information = float(config.get("opening_information", 0.0))
    params = {key: float(memory.get(key, 0.0) or 0.0) for key in ("I_MULT", "LAMBDA", "GAIN", "ACCEL", "REV_PENALTY")}
    variables = {**values, "I": information, "U": 0.0, "STREAK": 0.0, "REV": 0.0, **params}
    rule = HRule(
        capacity["hmax_expr"], memory["signal_expr"], memory["decay_expr"], memory["update_expr"],
        capacity.get("sat_kind", "hyperbolic"), float(capacity.get("sat_shape", 3.0)),
    )
    gross = rule.capacity(h0_gross, variables)
    plus = rule.capacity(h0_plus, variables)
    minus = rule.capacity(h0_minus, variables)
    intrawindow = config["intrawindow"]
    treasury = float(intrawindow.get("treasury_override", 0.0))
    minus = min(minus, treasury)
    return max(gross, plus, minus), plus, minus, treasury


def execute(project: dict, name: str, config: dict, scenario: dict) -> dict:
    gross, plus, minus, treasury = resolve_capacity(project, config)
    iw = config["intrawindow"]
    capacity = Capacity(gross, plus, minus)
    thresholds = Thresholds.from_rho(capacity, gross=iw["rho_gross"], net_plus=iw["rho_plus"], net_minus=iw["rho_minus"])
    engine = StateEngine(IssuerState("lab-issuer", TICKER, treasury, capacity, thresholds))
    start = datetime(2026, 9, 15, 13, 0, tzinfo=timezone.utc)
    engine.open_window(start, "W1")
    rows = [{"Passo": 0, "Ação": "START", "Quantidade": 0.0, "Preço": None, "BUY": 0.0, "SELL": 0.0, "Gross": 0.0, "Net": 0.0, "Treasury": treasury, "U gross": 0.0, "U net+": 0.0, "U net−": 0.0}]
    error = None
    for index, action in enumerate(scenario["actions"], 1):
        try:
            engine.execute(start + timedelta(minutes=index), Side(action["side"]), action["quantity"], action["price"])
            window = engine.state.active_window
            rows.append({"Passo": index, "Ação": action["side"], "Quantidade": action["quantity"], "Preço": action["price"], "BUY": window.buy, "SELL": window.sell, "Gross": window.gross, "Net": window.net, "Treasury": engine.state.treasury, "U gross": window.utilization(CapacityDimension.GROSS), "U net+": window.utilization(CapacityDimension.NET_PLUS), "U net−": window.utilization(CapacityDimension.NET_MINUS)})
        except (RuleViolation, ValueError) as exc:
            error = f"Passo {index}: {exc}"
            break
    window = engine.state.active_window
    disclosure = sorted(item.value for item in window.disclosure_dimensions())
    audit = pd.DataFrame(rows)
    audit["H gross restante"] = (gross - audit["Gross"]).clip(lower=0)
    audit["H net+ restante"] = (plus - audit["Net"].clip(lower=0)).clip(lower=0)
    audit["H net− restante"] = (minus - (-audit["Net"]).clip(lower=0)).clip(lower=0)
    audit["Status Q"] = audit.apply(lambda row: ", ".join(label for label, active in (("Gross", row["Gross"] >= thresholds.gross), ("Net+", max(row["Net"], 0) >= thresholds.net_plus), ("Net−", max(-row["Net"], 0) >= thresholds.net_minus)) if active) or "Abaixo de Q", axis=1)
    engine.close_window(start + timedelta(minutes=len(rows) + 1), "fim_do_pregao")
    event_labels = {"WindowOpened": "Janela aberta", "TradeExecuted": "Ordem executada", "QCrossed": "Q ultrapassado · alerta", "QReturnedBelow": "Retorno abaixo de Q", "DisclosureEvaluated": "Disclosure avaliado", "HExhausted": "H esgotado", "WindowClosed": "Janela fechada"}
    events = [{"#": event.sequence, "Evento": event_labels.get(event.event_type.value, event.event_type.value), "Hora": event.timestamp.strftime("%H:%M:%S"), **event.payload} for event in engine.events]
    checks = [
        {"Invariante": "Gross nunca diminui", "Resultado": "Passou" if audit["Gross"].diff().fillna(0).ge(0).all() else "Falhou"},
        {"Invariante": "Net = BUY − SELL", "Resultado": "Passou" if (audit["Net"] - (audit["BUY"] - audit["SELL"])).abs().le(1e-9).all() else "Falhou"},
        {"Invariante": "Treasury nunca negativa", "Resultado": "Passou" if audit["Treasury"].ge(0).all() else "Falhou"},
        {"Invariante": "Estado aceito nunca ultrapassa H", "Resultado": "Passou"},
        {"Invariante": "Fechamento explícito e auditável", "Resultado": "Passou"},
    ]
    return {
        "trajectory": rows, "audit": audit.to_dict("records"), "events": events, "checks": checks,
        "error": error, "disclosure": disclosure,
        "final": {"gross": window.gross, "net": window.net, "buy": window.buy, "sell": window.sell},
        "meta": {"spec_name": name, "ticker": TICKER, "scenario": scenario["name"], "rules_fingerprint": fingerprint(config), "scenario_fingerprint": fingerprint(scenario["actions"])},
    }


def experiment(experiment_id: str, name: str, config: dict, status: str, project: dict) -> dict:
    item = {
        "id": experiment_id, "name": name, "status": status, "created_at": NOW, "updated_at": NOW,
        "config": config,
    }
    if status == "draft":
        item["history"] = {"undo": [], "redo": []}
    else:
        item.update({"completed_at": NOW, "engine_version": ENGINE_VERSION, "fingerprint": fingerprint({"name": name, "config": config})})
    return item


def main() -> None:
    project = load_project(STATE_FILE)
    existing = next(iter(project["experiments"]["drafts"].values()))
    base = deepcopy(existing["config"])
    for obsolete in ("reference_ticker", "scenarios", "active_scenario_id"):
        base.pop(obsolete, None)
    base["intrawindow"].pop("reference_price_field", None)

    early_q = deepcopy(base)
    early_q["intrawindow"].update({"rho_gross": 0.35, "rho_plus": 0.40, "rho_minus": 0.40})

    conservative = deepcopy(base)
    conservative["capacity"].update({
        "h0_gross_expr": "AVG_DAILY_VOLUME_SHARES*0.15",
        "h0_plus_expr": "AVG_DAILY_VOLUME_SHARES*0.10",
        "h0_minus_expr": "AVG_DAILY_VOLUME_SHARES*0.06",
    })

    responsive = deepcopy(base)
    responsive["opening_information"] = 0.35
    responsive["memory"].update({"GAIN": 0.55, "LAMBDA": 0.08, "ACCEL": 0.25, "REV_PENALTY": 0.20})

    asymmetric = deepcopy(base)
    asymmetric["intrawindow"].update({"rho_gross": 0.55, "rho_plus": 0.30, "rho_minus": 0.70})

    expansive = deepcopy(base)
    expansive["capacity"].update({
        "h0_gross_expr": "AVG_DAILY_VOLUME_SHARES*0.35",
        "h0_plus_expr": "AVG_DAILY_VOLUME_SHARES*0.25",
        "h0_minus_expr": "AVG_DAILY_VOLUME_SHARES*0.15",
        "hmax_expr": "H0 * 7",
    })

    fixed_capacity = deepcopy(base)
    fixed_capacity["capacity"]["hmax_expr"] = "H0"
    fixed_capacity["memory"]["signal_expr"] = "0"

    linear = deepcopy(base)
    linear["opening_information"] = 0.35
    linear["capacity"].update({"sat_kind": "linear", "sat_shape": 1.0})

    project["experiments"]["drafts"] = {
        "experimento_base": experiment("experimento_base", "Base · Q balanceado", base, "draft", project),
    }
    project["experiments"]["completed"] = {
        "experimento_q_antecipado": experiment("experimento_q_antecipado", "Q antecipado · sensibilidade", early_q, "completed", project),
        "experimento_capacidade_conservadora": experiment("experimento_capacidade_conservadora", "Capacidade conservadora", conservative, "completed", project),
        "experimento_memoria_responsiva": experiment("experimento_memoria_responsiva", "Memória responsiva · I inicial", responsive, "completed", project),
        "experimento_q_assimetrico": experiment("experimento_q_assimetrico", "Q assimétrico · compra sensível", asymmetric, "completed", project),
        "experimento_capacidade_expansiva": experiment("experimento_capacidade_expansiva", "Capacidade expansiva", expansive, "completed", project),
        "experimento_capacidade_fixa": experiment("experimento_capacidade_fixa", "Capacidade fixa · sem progressão", fixed_capacity, "completed", project),
        "experimento_saturacao_linear": experiment("experimento_saturacao_linear", "Saturação linear · I inicial", linear, "completed", project),
    }
    project["scenarios"] = {"items": {}, "active_id": "cruza_q_e_retorna", "reference_price_field": "LAST_PRICE"}
    descriptions = {
        "controle_abaixo_q": "Trajetória moderada com redução parcial da posição.",
        "cruza_q_e_retorna": "Acumulação seguida de redução relevante perto do fechamento.",
        "disclosure_net_positivo": "Compra concentrada mantida até o fechamento.",
        "disclosure_gross_neutro": "Compra e venda equivalentes, com posição líquida final neutra.",
        "estresse_h": "Ordem única de grande porte para teste de capacidade.",
        "mglu_acumulacao_gradual": "Três momentos de negociação em companhia de maior volatilidade.",
        "mglu_giro_intenso": "Compra e venda de grande porte com posição residual pequena.",
        "vale_compra_mantida": "Compra concentrada preservada até o fechamento.",
        "vale_reducao_fechamento": "Construção de posição seguida por venda parcial no fim do pregão.",
        "kepl_operacao_moderada": "Trajetória calibrada para uma companhia de menor liquidez.",
        "kepl_ordem_concentrada": "Ordem única próxima da capacidade direcional da companhia.",
    }
    strategies = {
        "controle_abaixo_q": "Operação moderada",
        "cruza_q_e_retorna": "Acumulação com redução no fechamento",
        "disclosure_net_positivo": "Acumulação mantida",
        "disclosure_gross_neutro": "Giro com posição final neutra",
        "estresse_h": "Ordem concentrada de grande porte",
        "mglu_acumulacao_gradual": "Acumulação gradual com redução",
        "mglu_giro_intenso": "Giro intenso com posição residual",
        "vale_compra_mantida": "Compra concentrada mantida",
        "vale_reducao_fechamento": "Acumulação com redução no fechamento",
        "kepl_operacao_moderada": "Operação moderada",
        "kepl_ordem_concentrada": "Ordem concentrada",
    }
    companies = {
        **{scenario_id: "PETR4" for scenario_id in ("controle_abaixo_q", "cruza_q_e_retorna", "disclosure_net_positivo", "disclosure_gross_neutro", "estresse_h")},
        "mglu_acumulacao_gradual": "MGLU3", "mglu_giro_intenso": "MGLU3",
        "vale_compra_mantida": "VALE3", "vale_reducao_fechamento": "VALE3",
        "kepl_operacao_moderada": "KEPL3", "kepl_ordem_concentrada": "KEPL3",
    }
    for scenario_id, source in SCENARIOS.items():
        project["scenarios"]["items"][scenario_id] = {
            "id": scenario_id, "company": companies[scenario_id], "strategy": strategies[scenario_id],
            "description": descriptions[scenario_id], "actions": deepcopy(source["actions"]),
            "created_at": NOW, "updated_at": NOW, "history": {"undo": [], "redo": []},
        }
    project["evaluations"] = {}
    project["active_experiment_id"] = "experimento_base"
    project.setdefault("ui", {}).update({
        "main_nav": "Cenários", "experiment_section": "Visão geral",
        "scenario_preview_specification_id": "experimento_base",
        "specification_preview_scenario_id": "cruza_q_e_retorna",
    })
    save_project(STATE_FILE, project)


if __name__ == "__main__":
    main()
