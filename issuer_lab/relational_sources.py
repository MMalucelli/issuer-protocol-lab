from __future__ import annotations
import ast, json, re
from pathlib import Path
from typing import Any
import pandas as pd

_TOKEN = re.compile(r'\[([^\]]+)\]')
_ALLOWED_FUNCS = {'LEFT','RIGHT','SPLIT','REPLACE','CONCAT','UPPER','LOWER','TRIM','STR'}

def normalize_name(name:str)->str:
    s=str(name).strip()
    if not s: raise ValueError('nome vazio')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',s): raise ValueError('use letras, números e _; o nome deve começar por letra ou _')
    return s.upper()

def validate_unique_name(name:str, existing:list[str], ignore:str|None=None)->str:
    n=normalize_name(name); used={x.upper() for x in existing if not ignore or x.upper()!=ignore.upper()}
    if n in used: raise ValueError(f'{n} já existe na tabela-base')
    return n

def _flatten_record(d:dict[str,Any], prefix='')->dict[str,Any]:
    out={}
    for k,v in d.items():
        key=f'{prefix}.{k}' if prefix else str(k)
        if isinstance(v,dict): out.update(_flatten_record(v,key))
        else: out[key]=v
    return out

def _collections(obj:Any, path='root')->list[dict[str,Any]]:
    out=[]
    if isinstance(obj,list) and (not obj or all(isinstance(x,dict) for x in obj)):
        cols=sorted({k for r in obj[:50] for k in _flatten_record(r)}) if obj else []
        out.append({'path':path,'count':len(obj),'fields':cols})
    elif isinstance(obj,dict):
        # map-of-records is a useful relation too
        vals=list(obj.values())
        if vals and all(isinstance(v,dict) for v in vals):
            cols=sorted({k for r in vals[:50] for k in _flatten_record(r)})
            out.append({'path':path,'count':len(vals),'fields':cols,'map_keys':True})
        for k,v in obj.items(): out.extend(_collections(v, k if path=='root' else f'{path}.{k}'))
    return out

def _at_path(obj:Any,path:str)->Any:
    if not path or path=='root': return obj
    cur=obj
    for p in path.split('.'):
        cur=cur[int(p)] if isinstance(cur,list) else cur[p]
    return cur

def inspect_snapshot(path:Path)->dict[str,Any]:
    ext=path.suffix.lower()
    if ext=='.csv': df=pd.read_csv(path); return {'format':'CSV','collections':[{'path':'root','count':len(df),'fields':[str(c) for c in df.columns]}]}
    if ext in {'.xlsx','.xlsm'}:
        book=pd.ExcelFile(path,engine='openpyxl'); cols=[]
        for sh in book.sheet_names:
            df=pd.read_excel(path,sheet_name=sh,engine='openpyxl',nrows=20); cols.append({'path':sh,'count':len(pd.read_excel(path,sheet_name=sh,engine='openpyxl')),'fields':[str(c) for c in df.columns]})
        return {'format':'XLSX','collections':cols}
    if ext=='.json':
        obj=json.loads(path.read_text(encoding='utf-8-sig')); cs=_collections(obj)
        if not cs: cs=[{'path':'root','count':1,'fields':list(_flatten_record(obj)) if isinstance(obj,dict) else []}]
        return {'format':'JSON','collections':cs}
    raise ValueError('formato não suportado')

def header_candidates(path:Path, collection='root', max_rows:int=10)->list[dict[str,Any]]:
    """Return candidate header rows for tabular files, with a lightweight score.

    This is deliberately advisory: the UI exposes the candidates and lets the user override.
    """
    ext=path.suffix.lower()
    if ext not in {'.csv','.xlsx','.xlsm'}: return [{'row':0,'label':'root'}]
    raw = pd.read_csv(path, header=None, nrows=max_rows) if ext=='.csv' else pd.read_excel(path,sheet_name=collection,engine='openpyxl',header=None,nrows=max_rows)
    out=[]
    for i,row in raw.iterrows():
        vals=[x for x in row.tolist() if pd.notna(x) and str(x).strip()]
        if not vals: score=-1
        else:
            text=sum(isinstance(x,str) for x in vals)
            unique=len({str(x).strip().lower() for x in vals})
            score=(text/len(vals))+(unique/len(vals))+(min(len(vals),8)/8)
        preview=' | '.join(str(x)[:28] for x in vals[:5]) or '(vazia)'
        out.append({'row':int(i),'score':float(score),'preview':preview})
    return sorted(out,key=lambda x:(-x['score'],x['row']))

def suggested_header_row(path:Path, collection='root')->int:
    c=header_candidates(path,collection)
    return int(c[0]['row']) if c else 0

def load_relation(path:Path, collection='root', header_row:int=0)->pd.DataFrame:
    ext=path.suffix.lower()
    if ext=='.csv': return pd.read_csv(path, header=header_row)
    if ext in {'.xlsx','.xlsm'}: return pd.read_excel(path,sheet_name=collection,engine='openpyxl',header=header_row)
    if ext=='.json':
        obj=json.loads(path.read_text(encoding='utf-8-sig')); root=_at_path(obj,collection)
        if isinstance(root,list): return pd.DataFrame([_flatten_record(x) for x in root])
        if isinstance(root,dict):
            if root and all(isinstance(v,dict) for v in root.values()):
                rows=[]
                for key,val in root.items(): rows.append({'__key__':key,**_flatten_record(val)})
                return pd.DataFrame(rows)
            return pd.DataFrame([_flatten_record(root)])
    raise ValueError('coleção não tabular')

def _literal(node):
    if isinstance(node,ast.Constant): return node.value
    raise ValueError('literal inválido')

def eval_reference(expr:str,row:dict[str,Any])->str:
    """Small safe expression language. Fields are written [field]."""
    fields={}
    def repl(m):
        key=m.group(1); alias=f'__f{len(fields)}'; fields[alias]=row.get(key); return alias
    code=_TOKEN.sub(repl,expr.strip())
    tree=ast.parse(code,mode='eval')
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Name):
            if n.id in fields:return fields[n.id]
            raise ValueError(f'campo/função desconhecido: {n.id}')
        if isinstance(n,ast.Constant): return n.value
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add): return str(ev(n.left))+str(ev(n.right))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id.upper() in _ALLOWED_FUNCS:
            f=n.func.id.upper(); a=[ev(x) for x in n.args]
            if f=='LEFT': return str(a[1])[:int(a[0])]  # LEFT(5,[symbol])
            if f=='RIGHT': return str(a[1])[-int(a[0]):]
            if f=='SPLIT': return str(a[0]).split(str(a[1]))[int(a[2]) if len(a)>2 else 0]
            if f=='REPLACE': return str(a[0]).replace(str(a[1]),str(a[2]))
            if f=='CONCAT': return ''.join(str(x) for x in a)
            if f=='UPPER': return str(a[0]).upper()
            if f=='LOWER': return str(a[0]).lower()
            if f=='TRIM': return str(a[0]).strip()
            if f=='STR': return str(a[0])
        raise ValueError('expressão não permitida')
    return str(ev(tree))

def join_snapshot(base:pd.DataFrame, source:pd.DataFrame, base_ref:str, source_ref:str, selected:dict[str,str])->tuple[pd.DataFrame,dict[str,Any]]:
    if not selected: raise ValueError('selecione ao menos um campo')
    existing=list(base.columns)
    names=[]
    for src,dst in selected.items(): names.append(validate_unique_name(dst,existing+names))
    b=base.copy(); s=source.copy()
    b['__ref__']=[eval_reference(base_ref,r) for r in b.to_dict('records')]
    s['__ref__']=[eval_reference(source_ref,r) for r in s.to_dict('records')]
    dup=s['__ref__'].duplicated(keep=False)
    if dup.any(): raise ValueError(f'referência da source não é única: {s.loc[dup,"__ref__"].iloc[0]}')
    mapping=s.set_index('__ref__')
    matched=b['__ref__'].isin(mapping.index)
    for (src,dst),norm in zip(selected.items(),names):
        if src not in s.columns: raise ValueError(f'campo ausente: {src}')
        b[norm]=b['__ref__'].map(mapping[src])
    stats={'matched':int(matched.sum()),'total':len(b),'unmatched':b.loc[~matched,'__ref__'].tolist()}
    return b.drop(columns='__ref__'),stats

FUNCTION_HELP={
 'LEFT':'LEFT(5, [symbol]) — devolve os primeiros 5 caracteres. O tamanho deve ser numérico: `5`, não `"cinco"`.',
 'RIGHT':'RIGHT(2, [symbol]) — devolve os últimos 2 caracteres.',
 'SPLIT':'SPLIT([symbol], ".", 0) — separa o texto pelo delimitador e escolhe a parte pelo índice; índices começam em 0.',
 'REPLACE':'REPLACE([symbol], ".SA", "") — substitui um trecho literal por outro; use aspas para texto.',
 'CONCAT':'CONCAT([ticker], ":", [exchange]) — concatena campos e/ou textos na ordem informada.',
 'UPPER':'UPPER([symbol]) — converte texto para maiúsculas.',
 'LOWER':'LOWER([symbol]) — converte texto para minúsculas.',
 'TRIM':'TRIM([symbol]) — remove espaços no início e no fim do texto.',
 'STR':'STR([campo]) — converte um valor não textual (por exemplo, número/data já representável) em texto para permitir composição com outras partes.'
}


def build_base_snapshot(source: pd.DataFrame, reference: str, *, origin: str, existing_manual: pd.DataFrame | None = None) -> pd.DataFrame:
    """Freeze a canonical one-column asset universe from a source relation.

    Imported rows carry provenance; manual rows may be preserved across a source replacement.
    The canonical public field is always main_id.
    """
    ids=[]
    for row in source.to_dict('records'):
        value=eval_reference(reference,row).strip()
        if value and value not in ids: ids.append(value)
    rows=[{'main_id':x,'__base_origin__':'import','__base_detail__':origin} for x in ids]
    if existing_manual is not None and not existing_manual.empty:
        for row in existing_manual.to_dict('records'):
            mid=str(row.get('main_id','')).strip()
            if mid and mid not in ids:
                rows.append({'main_id':mid,'__base_origin__':'manual','__base_detail__':'manual'})
                ids.append(mid)
    return pd.DataFrame(rows,columns=['main_id','__base_origin__','__base_detail__'])

def add_manual_base_ids(base: pd.DataFrame, values: list[str]) -> pd.DataFrame:
    out=base.copy() if base is not None else pd.DataFrame(columns=['main_id','__base_origin__','__base_detail__'])
    existing=set(out.get('main_id',pd.Series(dtype=str)).astype(str))
    add=[]
    for raw in values:
        value=str(raw).strip()
        if value and value not in existing:
            add.append({'main_id':value,'__base_origin__':'manual','__base_detail__':'manual'}); existing.add(value)
    result=pd.concat([out,pd.DataFrame(add)],ignore_index=True) if add else out
    return canonical_base_columns(result)

def canonical_base_columns(base: pd.DataFrame) -> pd.DataFrame:
    """Keep the public identifier first and internal metadata last."""
    if base is None:
        return pd.DataFrame(columns=['main_id','__base_origin__','__base_detail__'])
    columns=list(base.columns)
    identifier=['main_id'] if 'main_id' in columns else []
    public=[c for c in columns if c!='main_id' and not str(c).startswith('__')]
    metadata=[c for c in columns if str(c).startswith('__')]
    return base.loc[:,identifier+public+metadata].copy()

def visible_base(base: pd.DataFrame) -> pd.DataFrame:
    ordered=canonical_base_columns(base)
    return ordered[[c for c in ordered.columns if not str(c).startswith('__')]].copy()

def provenance_description(metadata: dict[str, Any] | None) -> str:
    """Human description for an observed column, with an explicit source fallback."""
    meta=metadata or {}
    description=str(meta.get('description','') or '').strip()
    if description: return description
    source=str(meta.get('source','tabela-base') or 'tabela-base').strip()
    field=str(meta.get('field','') or '').strip()
    detail=source + (f' · {field}' if field and field.casefold()!=source.casefold() else '')
    return f'Fonte: {detail}'
