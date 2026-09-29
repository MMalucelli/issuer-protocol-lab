from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

@dataclass(frozen=True)
class Observation:
    variable: str
    ticker: str
    value: float
    unit: str
    source: str
    fetched_at: str
    field: str = ''
    transform: str = 'identity'

@dataclass(frozen=True)
class SourceSpec:
    variable: str
    provider: str = 'Snapshot local'
    unit: str = ''
    endpoint: str = ''
    field: str = ''
    scale: float = 1.0
    manual_value: float = 0.0
    template_vars: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    local_file: str = 'market_snapshot.json'
    collection: str = ''
    identifier_field: str = ''
    identifier_template: str = '{ticker}'


def _path(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split('.') if path else []:
        if isinstance(cur, list): cur = cur[int(part)]
        else: cur = cur[part]
    return cur


def render_template(text: str, ticker: str, template_vars: dict[str,str] | None=None) -> str:
    context={'ticker': ticker, **(template_vars or {})}
    try:
        return text.format_map(context)
    except KeyError as exc:
        raise ValueError(f'placeholder sem valor: {{{exc.args[0]}}}') from exc


def fetch_json(url: str, timeout: float = 8.0, headers: dict[str,str] | None=None) -> Any:
    if not url.lower().startswith(('https://','http://')):
        raise ValueError('endpoint deve começar com http:// ou https://')
    merged={'User-Agent':'IssuerProtocolLab/0.3', **(headers or {})}
    req=Request(url, headers=merged)
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def test_api_source(spec: SourceSpec, ticker: str) -> dict[str,Any]:
    if spec.provider != 'API JSON': raise ValueError('o teste de conexão requer Provider = API JSON')
    url=render_template(spec.endpoint,ticker,spec.template_vars)
    headers={k:render_template(v,ticker,spec.template_vars) for k,v in (spec.headers or {}).items()}
    payload=fetch_json(url,headers=headers)
    raw=_path(payload,spec.field)
    value=float(raw)*float(spec.scale)
    return {'url':url,'raw_value':raw,'value':value,'payload':payload}


def discover_local_sources(sources_dir: Path) -> list[str]:
    sources_dir.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in sources_dir.iterdir() if p.is_file() and p.suffix.lower() in {'.json','.csv','.xlsx','.xlsm'})


def _load_local(path: Path) -> Any:
    if path.suffix.lower()=='.json': return json.loads(path.read_text(encoding='utf-8-sig'))
    if path.suffix.lower()=='.csv':
        with path.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
    raise ValueError('formato local não suportado; use .json ou .csv')


def inspect_local_source(path: Path) -> dict[str,Any]:
    data=_load_local(path)
    if path.suffix.lower()=='.csv':
        columns=list(data[0]) if data else []
        return {'format':'CSV','kind':'records','columns':columns,'count':len(data),'preview':data[:5]}
    # JSON: expose useful top-level collection candidates without pretending to infer semantics.
    candidates=[]
    if isinstance(data,dict):
        for k,v in data.items():
            if isinstance(v,(list,dict)): candidates.append(k)
    return {'format':'JSON','kind':type(data).__name__,'top_keys':list(data)[:30] if isinstance(data,dict) else [],'collections':candidates,'preview':data}


def _select_local_record(data: Any, ticker: str, collection: str, identifier_field: str, identifier_template: str, template_vars: dict[str,str]|None) -> tuple[Any,str]:
    root=_path(data,collection) if collection else data
    wanted=render_template(identifier_template or '{ticker}',ticker,template_vars)
    if isinstance(root,dict):
        if identifier_field:
            for key,record in root.items():
                if isinstance(record,dict) and str(_path(record,identifier_field))==wanted: return record,str(key)
            raise ValueError(f'identificador {wanted!r} não encontrado em {identifier_field}')
        if wanted not in root: raise ValueError(f'chave {wanted!r} não encontrada')
        return root[wanted],wanted
    if isinstance(root,list):
        if not identifier_field: raise ValueError('coleção em lista requer Campo identificador')
        for idx,record in enumerate(root):
            if isinstance(record,dict) and str(_path(record,identifier_field))==wanted: return record,str(idx)
        raise ValueError(f'identificador {wanted!r} não encontrado em {identifier_field}')
    raise ValueError('coleção selecionada não é uma coleção de registros')


def test_local_source(spec: SourceSpec, ticker: str, sources_dir: Path) -> dict[str,Any]:
    if spec.provider != 'Arquivo local': raise ValueError('o teste local requer Provider = Arquivo local')
    path=(sources_dir/spec.local_file).resolve()
    base=sources_dir.resolve()
    if base not in path.parents: raise ValueError('arquivo deve estar dentro de data/sources')
    if not path.exists(): raise ValueError(f'arquivo não encontrado: {spec.local_file}')
    data=_load_local(path)
    record,record_id=_select_local_record(data,ticker,spec.collection,spec.identifier_field,spec.identifier_template,spec.template_vars)
    raw=_path(record,spec.field)
    value=float(raw)*float(spec.scale)
    return {'file':spec.local_file,'record_id':record_id,'raw_value':raw,'value':value,'record':record}


def resolve_observation(spec: SourceSpec, ticker: str, snapshot_values: dict[str,float]|None=None, now: str|None=None, sources_dir: Path|None=None) -> Observation:
    ts=now or datetime.now(timezone.utc).isoformat()
    # Legacy snapshot provider remains readable for imported old specifications.
    if spec.provider == 'Snapshot local':
        values=snapshot_values or {}
        if spec.variable not in values: raise ValueError(f'{spec.variable} não existe no snapshot')
        value=float(values[spec.variable])*float(spec.scale); source='market_snapshot.json'; field=spec.variable
    elif spec.provider == 'Arquivo local':
        if sources_dir is None: raise ValueError('sources_dir é obrigatório para Arquivo local')
        tested=test_local_source(spec,ticker,sources_dir)
        value=float(tested['value']); source=f'data/sources/{spec.local_file}'; field=spec.field
        return Observation(spec.variable,ticker,value,spec.unit,source,ts,field,f'x {spec.scale:g}')
    elif spec.provider == 'Manual':
        value=float(spec.manual_value)*float(spec.scale); source='entrada manual'; field='manual_value'
    elif spec.provider == 'API JSON':
        tested=test_api_source(spec,ticker)
        value=float(tested['value']); source=str(tested['url']); field=spec.field
        return Observation(spec.variable,ticker,value,spec.unit,source,ts,field,f'x {spec.scale:g}')
    else:
        raise ValueError(f'provider desconhecido: {spec.provider}')
    return Observation(spec.variable,ticker,value,spec.unit,source,ts,field,f'x {spec.scale:g}')


def observation_dict(obs: Observation) -> dict[str,Any]: return asdict(obs)
