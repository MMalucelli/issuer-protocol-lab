from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Any

WORKSPACE_VERSION=1
HISTORY_LIMIT=50
HISTORY_KEY="_history"
VOLATILE_KEYS={"main_nav","iw_ticker","iw_config","iw_opening_information","exp_ticker","exp_information","exp_config"}

def _state(data: dict[str, Any]) -> dict[str, Any]:
    return {k:v for k,v in data.items() if k not in {"workspace_version",HISTORY_KEY}}

def _semantic(data: dict[str, Any]) -> dict[str, Any]:
    return {k:v for k,v in _state(data).items() if k not in VOLATILE_KEYS}

def _history(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw=data.get(HISTORY_KEY,{})
    if not isinstance(raw,dict): raw={}
    undo=raw.get("undo",[]); redo=raw.get("redo",[])
    return {
        "undo":list(undo) if isinstance(undo,list) else [],
        "redo":list(redo) if isinstance(redo,list) else [],
    }

def _write(path: Path, state: dict[str, Any], history: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    document={"workspace_version":WORKSPACE_VERSION,**state,HISTORY_KEY:history}
    body=json.dumps(document,ensure_ascii=False,indent=2,sort_keys=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:
            handle.write(body); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_workspace(path: Path) -> dict[str, Any]:
    if not path.exists(): return {}
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,dict): return {}
        return data
    except (OSError,json.JSONDecodeError):
        return {}

def save_workspace(path: Path, payload: dict[str, Any]) -> None:
    """Atomically save current state and retain semantic revisions in the same JSON."""
    existing=load_workspace(path)
    current=_state(existing); incoming=_state(payload); history=_history(existing)
    if current==incoming: return
    if current and _semantic(current)!=_semantic(incoming):
        history["undo"]=(history["undo"]+[current])[-HISTORY_LIMIT:]
        history["redo"]=[]
    _write(path,incoming,history)

def history_status(path: Path) -> tuple[int,int]:
    history=_history(load_workspace(path))
    return len(history["undo"]),len(history["redo"])

def undo_workspace(path: Path) -> dict[str, Any] | None:
    document=load_workspace(path); history=_history(document)
    if not history["undo"]: return None
    current=_state(document); restored=history["undo"].pop()
    for key in VOLATILE_KEYS:
        if key in current: restored[key]=current[key]
    history["redo"]=(history["redo"]+[current])[-HISTORY_LIMIT:]
    _write(path,restored,history)
    return restored

def redo_workspace(path: Path) -> dict[str, Any] | None:
    document=load_workspace(path); history=_history(document)
    if not history["redo"]: return None
    current=_state(document); restored=history["redo"].pop()
    for key in VOLATILE_KEYS:
        if key in current: restored[key]=current[key]
    history["undo"]=(history["undo"]+[current])[-HISTORY_LIMIT:]
    _write(path,restored,history)
    return restored
