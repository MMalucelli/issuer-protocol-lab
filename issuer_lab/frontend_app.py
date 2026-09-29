from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import json, sys, hashlib
import math
from pathlib import Path
import pandas as pd
import altair as alt
import streamlit as st

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from issuer_lab import Capacity,CapacityDimension,IssuerState,RuleViolation,Side,StateEngine,Thresholds
from issuer_lab.capacity_builder import MarketMetrics,HRule
from issuer_lab.expression_engine import evaluate, endpoint_saturation, evaluate_derived, explain_dependency, dependency_layers, dependency_graph, direct_dependents
from issuer_lab.data_sources import SourceSpec, resolve_observation, test_api_source, test_local_source, discover_local_sources, inspect_local_source
from issuer_lab.relational_sources import inspect_snapshot, load_relation, eval_reference, join_snapshot, FUNCTION_HELP, validate_unique_name, build_base_snapshot, add_manual_base_ids, visible_base, canonical_base_columns, header_candidates, suggested_header_row, provenance_description
from issuer_lab.specification import LabSpecification
from issuer_lab.scenario_utils import apply_editor_delta, comparison_projection, executable_actions, available_comparison_pairs, semantic_field_options
from issuer_lab.project_store import (
    adopt_global_treasury_mapping,
    active_draft, active_scenario, commit_active_experiment, commit_active_scenario, commit_foundation, create_draft, create_scenario,
    delete_experiment, delete_scenario, restore_scenario, duplicate_as_draft, reopen_completed, finalize_active, flat_view,
    foundation_snapshot, history_status, load_project, redo, save_project, undo,
)

st.set_page_config(page_title='Issuer Protocol Lab',page_icon='◫',layout='wide')
st.markdown('''<style>.block-container{max-width:1780px;padding-top:1.5rem} h1{letter-spacing:-.04em}.muted{opacity:.68}.eyebrow{opacity:.62;font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700}.st-key-leftscroll,.st-key-rightscroll,.st-key-rel_base_ref_palette,.st-key-rel_src_ref_palette{scrollbar-width:thin}.st-key-rel_base_ref_palette,.st-key-rel_src_ref_palette{max-height:15rem;overflow-y:auto;padding-right:.25rem}</style>''',unsafe_allow_html=True)

SNAPSHOT=ROOT/'market_snapshot.json'
SOURCES_DIR=ROOT/'data'/'sources'
# Single canonical project file. Base/variables and each experiment have
# independent revision histories inside it.
WORKSPACE_FILE=ROOT/'lab_state.json'
if st.session_state.get('_restore_notice'):
    st.toast(st.session_state.pop('_restore_notice'))

def load_market():
    raw=json.loads(SNAPSHOT.read_text(encoding='utf-8')) if SNAPSHOT.exists() else {'tickers':{}}
    out={}
    for t,v in raw.get('tickers',{}).items():
        x=v.get('metrics',{})
        out[t]=MarketMetrics(t,float(x.get('avg_daily_volume_shares',0)),float(x.get('last_price',0)),None if x.get('float_shares') is None else float(x['float_shares']),float(x.get('avg_daily_turnover_brl',0)),float(x.get('annualized_volatility',0)))
    return out,raw
MARKET,MARKET_RAW=load_market()

@dataclass(frozen=True)
class Config:
    name:str; h_gross:float; h_plus:float; h_minus:float; rho_gross:float; rho_plus:float; rho_minus:float; treasury:float

# Undo/redo is requested by a widget that already belongs to the previous UI
# tree. Consume the restored snapshot before recreating any stateful widget, so
# stale browser values cannot overwrite the restored file on the next rerun.
_pending_project=st.session_state.pop('_pending_project',None)
if _pending_project is not None:
    st.session_state.clear()
    st.session_state._project=_pending_project
    st.session_state._workspace_saved=flat_view(_pending_project)
    st.session_state._workspace_bootstrapped=True
elif '_workspace_bootstrapped' not in st.session_state:
    st.session_state._project=load_project(WORKSPACE_FILE)
    st.session_state._workspace_saved=flat_view(st.session_state._project)
    st.session_state._workspace_bootstrapped=True

DEFAULTS={
 'Baseline':Config('Baseline',200_000,150_000,100_000,.5,.5,.5,80_000),
 'Q antecipado':Config('Q antecipado',200_000,150_000,100_000,.25,.25,.25,80_000),
 'Gross restritivo':Config('Gross restritivo',150_000,150_000,100_000,.5,.5,.5,80_000),
}
_saved=st.session_state._workspace_saved
if 'configs' not in st.session_state:
    raw_configs=_saved.get('configs',{})
    st.session_state.configs={name:Config(name,**data) for name,data in raw_configs.items()} if raw_configs else DEFAULTS.copy()
if 'actions' not in st.session_state: st.session_state.actions=list(_saved.get('actions',[{'side':'BUY','quantity':40_000.0,'price':10.0},{'side':'BUY','quantity':35_000.0,'price':10.2},{'side':'SELL','quantity':20_000.0,'price':10.5}]))
if 'sector_meta' not in st.session_state:
    st.session_state.sector_meta={
      'PETR4':('Petróleo',1.00),'VALE3':('Mineração',1.00),'BBSE3':('Seguros',1.00),'MGLU3':('Varejo',1.00),
      'ITUB4':('Bancos',1.00),'BBAS3':('Bancos',1.00),'WEGE3':('Indústria',1.00),'BBDC4':('Bancos',1.00),
      'ABEV3':('Bebidas',1.00),'SUZB3':('Papel e celulose',1.00),'KEPL3':('Bens de capital',1.00)}
if 'h0_gross_expr' not in st.session_state: st.session_state.h0_gross_expr=_saved.get('h0_gross_expr','')
if 'h0_plus_expr' not in st.session_state: st.session_state.h0_plus_expr=_saved.get('h0_plus_expr','')
if 'h0_minus_expr' not in st.session_state: st.session_state.h0_minus_expr=_saved.get('h0_minus_expr','')
if 'hmax_expr' not in st.session_state: st.session_state.hmax_expr=_saved.get('hmax_expr','H0 * 5')
if 'signal_expr' not in st.session_state: st.session_state.signal_expr=_saved.get('signal_expr','clamp(I * I_MULT, 0, 1)')
if 'decay_expr' not in st.session_state: st.session_state.decay_expr=_saved.get('decay_expr','I * exp(-LAMBDA * DT)')
if 'update_expr' not in st.session_state: st.session_state.update_expr=_saved.get('update_expr','I_DECAYED + U * GAIN * (1 + ACCEL * max(STREAK - 1, 0)) * (1 - REV * REV_PENALTY)')
for _key,_default in {'GAIN':.35,'LAMBDA':.15,'ACCEL':.15,'REV_PENALTY':.30,'I_MULT':1.0,'sat_shape':3.0,'sat_kind':'hyperbolic'}.items():
    if _key not in st.session_state: st.session_state[_key]=_saved.get(_key,_default)
if 'iw_opening_information' not in st.session_state: st.session_state.iw_opening_information=float(_saved.get('iw_opening_information',0.0))
if 'iw_ticker' not in st.session_state and _saved.get('iw_ticker'): st.session_state.iw_ticker=_saved['iw_ticker']
if 'iw_config' not in st.session_state and _saved.get('iw_config'): st.session_state.iw_config=_saved['iw_config']
if 'exp_information' not in st.session_state: st.session_state.exp_information=float(_saved.get('exp_information',0.0))
if 'exp_ticker' not in st.session_state and _saved.get('exp_ticker'): st.session_state.exp_ticker=_saved['exp_ticker']
if 'exp_config' not in st.session_state and _saved.get('exp_config'): st.session_state.exp_config=_saved['exp_config']
if 'spec_name' not in st.session_state: st.session_state.spec_name=str(_saved.get('spec_name','Working specification'))
# Bind the name widget to the active draft identity. The manager has no active
# draft and therefore legitimately carries an empty flat-view name; that empty
# value must not leak into a draft when it is opened on the following rerun.
_active_draft_id=st.session_state._project.get('active_experiment_id')
_active_draft_for_name=active_draft(st.session_state._project)
if _active_draft_for_name:
    _draft_changed=st.session_state.get('_spec_name_draft_id')!=_active_draft_id
    _name_missing=not str(st.session_state.get('spec_name') or '').strip()
    if _draft_changed or _name_missing:
        st.session_state.spec_name=str(_active_draft_for_name.get('name') or 'Nova especificação')
    st.session_state._spec_name_draft_id=_active_draft_id
else:
    st.session_state._spec_name_draft_id=None
if 'main_nav' not in st.session_state and _saved.get('main_nav'): st.session_state.main_nav=_saved['main_nav']
if 'active_scenario_id' not in st.session_state: st.session_state.active_scenario_id=_saved.get('active_scenario_id')
if 'semantic_mappings' not in st.session_state: st.session_state.semantic_mappings=dict(_saved.get('semantic_mappings',{}))
if 'treasury_override_enabled' not in st.session_state: st.session_state.treasury_override_enabled=bool(_saved.get('treasury_override_enabled',False))
if 'treasury_override_explicit' not in st.session_state: st.session_state.treasury_override_explicit=bool(_saved.get('treasury_override_explicit',False))
if 'treasury_override' not in st.session_state: st.session_state.treasury_override=float(_saved.get('treasury_override',0.0) or 0.0)
if 'position_limit_enabled' not in st.session_state: st.session_state.position_limit_enabled=bool(_saved.get('position_limit_enabled',False))
if 'position_limit_ratio' not in st.session_state: st.session_state.position_limit_ratio=float(_saved.get('position_limit_ratio',25.0) or 25.0)
if 'position_limit_field' not in st.session_state: st.session_state.position_limit_field=_saved.get('position_limit_field')

def semantic_mapping(role):
    return st.session_state.get('semantic_mappings',{}).get(role)

def make_engine(c):
    h=Capacity(c.h_gross,c.h_plus,c.h_minus); q=Thresholds.from_rho(h,gross=c.rho_gross,net_plus=c.rho_plus,net_minus=c.rho_minus)
    e=StateEngine(IssuerState('lab-issuer','LAB3',c.treasury,h,q)); e.open_window(datetime(2026,9,15,13,0,tzinfo=timezone.utc),'W1'); return e

def run(c,actions):
    e=make_engine(c); w=e.state.active_window
    rows=[{'Passo':0,'Ação':'START','Solicitada':0.,'Quantidade':0.,'Rejeitada':0.,'Status':'Estado inicial','Limites':'','Preço':None,'BUY':0.,'SELL':0.,'Gross':0.,'Net':0.,'Gross solicitado':0.,'Net solicitado':0.,'Treasury':e.state.treasury,'U gross':0.,'U net+':0.,'U net−':0.}]; error=None; capacity_notices=[]
    start=datetime(2026,9,15,13,0,tzinfo=timezone.utc)
    for idx,a in enumerate(actions,1):
        try:
            side=Side(a['side']); requested=float(a['quantity']); pre_gross=w.gross; pre_net=w.net
            requested_gross=pre_gross+requested; requested_net=pre_net+(requested if side is Side.BUY else -requested)
            limits=e.execution_limits(side); executable=min(requested,min(limits.values()))
            binding=[name for name,value in limits.items() if abs(value-executable)<=1e-9] if executable+1e-9<requested else []
            if executable>1e-9: e.execute(start+timedelta(minutes=idx),side,executable,float(a['price']))
            w=e.state.active_window
            rejected=max(0.,requested-executable); status='Executada integralmente'; limit_text=''
            if executable+1e-9<requested:
                labels={'gross':'Gross','net_plus':'Net+','net_minus':'Net−','treasury':'ações em tesouraria'}
                limit_text=', '.join(labels[name] for name in binding)
                status=('Execução parcial' if executable>1e-9 else 'Não executada')+' · excederia 100% de H: '+limit_text
                capacity_notices.append({'passo':idx,'lado':side.value,'solicitada':requested,'executada':executable,'rejeitada':rejected,'limites':[labels[name] for name in binding]})
            rows.append({'Passo':idx,'Ação':a['side'],'Solicitada':requested,'Quantidade':executable,'Rejeitada':rejected,'Status':status,'Limites':limit_text,'Preço':float(a['price']),'BUY':w.buy,'SELL':w.sell,'Gross':w.gross,'Net':w.net,'Gross solicitado':requested_gross,'Net solicitado':requested_net,'Treasury':e.state.treasury,'U gross':w.utilization(CapacityDimension.GROSS),'U net+':w.utilization(CapacityDimension.NET_PLUS),'U net−':w.utilization(CapacityDimension.NET_MINUS)})
        except (RuleViolation,ValueError) as exc: error=f'Passo {idx}: {exc}'; break
    return e,pd.DataFrame(rows),error,capacity_notices

def rules_fingerprint(payload):
    canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:12]

def execute_experiment(config,actions):
    engine,trajectory,error,capacity_notices=run(config,actions)
    window=engine.state.active_window
    disclosure=window.disclosure_dimensions()
    audit=trajectory.copy()
    audit['H gross restante']=(config.h_gross-audit['Gross']).clip(lower=0)
    audit['H net+ restante']=(config.h_plus-audit['Net'].clip(lower=0)).clip(lower=0)
    audit['H net− restante']=(config.h_minus-(-audit['Net']).clip(lower=0)).clip(lower=0)
    audit['Status Q']=audit.apply(lambda row:', '.join(x for x,active in [('Gross',row['Gross']>=config.h_gross*config.rho_gross),('Net+',max(row['Net'],0)>=config.h_plus*config.rho_plus),('Net−',max(-row['Net'],0)>=config.h_minus*config.rho_minus)] if active) or 'Abaixo de Q',axis=1)
    close_at=datetime(2026,9,15,13,0,tzinfo=timezone.utc)+timedelta(minutes=len(trajectory)+1)
    engine.close_window(close_at,'fim_do_pregao')
    event_labels={'WindowOpened':'Janela aberta','TradeExecuted':'Ordem executada','QCrossed':'Q ultrapassado · alerta','QReturnedBelow':'Retorno abaixo de Q','DisclosureEvaluated':'Disclosure avaliado','HExhausted':'H esgotado','WindowClosed':'Janela fechada'}
    events=pd.DataFrame([{'#':event.sequence,'Evento':event_labels.get(event.event_type.value,event.event_type.value),'Hora':event.timestamp.strftime('%H:%M:%S'),**event.payload} for event in engine.events])
    checks=[
        {'Invariante':'Gross nunca diminui','Resultado':'Passou' if audit['Gross'].diff().fillna(0).ge(0).all() else 'Falhou'},
        {'Invariante':'Net = BUY − SELL','Resultado':'Passou' if (audit['Net']-(audit['BUY']-audit['SELL'])).abs().le(1e-9).all() else 'Falhou'},
        {'Invariante':'Treasury nunca negativa','Resultado':'Passou' if audit['Treasury'].ge(0).all() else 'Falhou'},
        {'Invariante':'Estado aceito nunca ultrapassa H','Resultado':'Passou' if audit['Gross'].le(config.h_gross+1e-9).all() and audit['Net'].clip(lower=0).le(config.h_plus+1e-9).all() and (-audit['Net']).clip(lower=0).le(config.h_minus+1e-9).all() else 'Falhou'},
        {'Invariante':'Fechamento explícito e auditável','Resultado':'Passou' if not events.empty and events.iloc[-1]['Evento']=='Janela fechada' else 'Falhou'},
    ]
    return {'trajectory':trajectory,'audit':audit,'events':events,'checks':pd.DataFrame(checks),'error':error,'capacity_notices':capacity_notices,'disclosure':sorted(x.value for x in disclosure),'final_window':window}

def dimension_labels(dimensions):
    labels={'gross':'Gross','net_plus':'Net+','net_minus':'Net−'}
    return [labels.get(value,value) for value in dimensions]

def disclosure_status(dimensions):
    labels=dimension_labels(dimensions)
    return 'Divulgação no fechamento: '+ ' e '.join(labels) if labels else 'Sem divulgação no fechamento'

def capacity_status(notices):
    limits=[]
    for notice in notices:
        for limit in notice.get('limites',[]):
            if limit not in limits: limits.append(limit)
    return 'Capacidade máxima atingida: '+', '.join(limits) if limits else ''

def execution_status(result):
    trajectory=result['trajectory']; orders=trajectory[trajectory['Passo']>0]
    requested=float(orders['Solicitada'].sum()); executed=float(orders['Quantidade'].sum()); rejected=float(orders['Rejeitada'].sum())
    partial=int(orders['Status'].str.startswith('Execução parcial').sum()); denied=int(orders['Status'].str.startswith('Não executada').sum())
    integral=len(orders)-partial-denied
    parts=[f'{executed:,.0f} de {requested:,.0f} executadas',f'{integral} '+('integral' if integral==1 else 'integrais')]
    if partial: parts.append(f'{partial} '+('parcial' if partial==1 else 'parciais'))
    if denied: parts.append(f'{denied} '+('rejeitada' if denied==1 else 'rejeitadas'))
    if rejected>0: parts.append(f'{rejected:,.0f} não executadas')
    return ' · '.join(parts)

def line_chart(df,cols):
    if df is None or df.empty or not cols:
        st.info('Não há pontos válidos para desenhar esta trajetória.')
        return
    long=df[['Passo']+cols].melt('Passo',var_name='Série',value_name='Valor')
    long=long.dropna(subset=['Passo','Valor'])
    if long.empty:
        st.info('Não há valores numéricos válidos para desenhar esta trajetória.')
        return
    mx=max(int(df['Passo'].max()),1)
    chart=alt.Chart(long).mark_line(point=True).encode(x=alt.X('Passo:Q',scale=alt.Scale(domain=[0,mx]),axis=alt.Axis(tickMinStep=1)),y='Valor:Q',color='Série:N',tooltip=['Passo','Série','Valor']).properties(height=330)
    st.altair_chart(chart,width='stretch')

def intrawindow_chart(df,config):
    rows=[]; rejected_rows=[]
    last_step=df['Passo'].max() if not df.empty else 0
    for _,row in df.iterrows():
        for dimension,utilization,q in [
            ('Gross',row['Gross']/config.h_gross if config.h_gross else 0.,config.rho_gross),
            ('Net+',max(row['Net'],0)/config.h_plus if config.h_plus else 0.,config.rho_plus),
            ('Net−',max(-row['Net'],0)/config.h_minus if config.h_minus else 0.,config.rho_minus),
        ]:
            rows.append({'Passo':row['Passo'],'Dimensão':dimension,'Utilização':utilization,'Q':q,'Disclosure':row['Passo']==last_step and utilization>=q})
            if float(row.get('Rejeitada',0.) or 0.)>0 and dimension in str(row.get('Limites','')):
                requested={'Gross':float(row['Gross solicitado'])/config.h_gross if config.h_gross else 0.,'Net+':max(float(row['Net solicitado']),0.)/config.h_plus if config.h_plus else 0.,'Net−':max(-float(row['Net solicitado']),0.)/config.h_minus if config.h_minus else 0.}[dimension]
                rejected_rows.append({'Passo':row['Passo'],'Dimensão':dimension,'Executada':utilization,'Solicitada':requested,'Quantidade solicitada':row['Solicitada'],'Quantidade executada':row['Quantidade'],'Quantidade rejeitada':row['Rejeitada'],'Motivo':'Excederia 100% de H '+dimension})
    data=pd.DataFrame(rows)
    rejected=pd.DataFrame(rejected_rows)
    y_max=max(1.05,float(rejected['Solicitada'].max())*1.08 if not rejected.empty else 1.05)
    trajectory=alt.Chart(data).mark_line(point=True).encode(
        x=alt.X('Passo:Q',axis=alt.Axis(tickMinStep=1)),y=alt.Y('Utilização:Q',axis=alt.Axis(format='%'),scale=alt.Scale(domain=[0,y_max])),
        color='Dimensão:N',tooltip=['Passo','Dimensão',alt.Tooltip('Utilização:Q',format='.1%')])
    thresholds=alt.Chart(data.drop_duplicates('Dimensão')).mark_rule(strokeDash=[6,4]).encode(
        y='Q:Q',color='Dimensão:N',tooltip=['Dimensão',alt.Tooltip('Q:Q',format='.1%')])
    hard_cap=alt.Chart(pd.DataFrame([{'H':1.0}])).mark_rule(color='#ff4b4b',strokeWidth=2).encode(y='H:Q')
    layers=[trajectory,thresholds,hard_cap]
    disclosed=data[data['Disclosure']]
    if not disclosed.empty:
        layers.extend([
            alt.Chart(disclosed).mark_point(shape='diamond',size=180,filled=True,color='#ff4b4b').encode(x='Passo:Q',y='Utilização:Q',tooltip=['Dimensão',alt.Tooltip('Utilização:Q',format='.1%')]),
            alt.Chart(disclosed).mark_text(text='Divulgação',dy=-14,color='#ff4b4b',fontWeight='bold').encode(x='Passo:Q',y='Utilização:Q'),
        ])
    if not rejected.empty:
        layers.extend([
            alt.Chart(rejected).mark_rule(color='#ff4b4b',strokeDash=[4,3],strokeWidth=3).encode(x='Passo:Q',y='Executada:Q',y2='Solicitada:Q'),
            alt.Chart(rejected).mark_point(shape='cross',size=220,strokeWidth=4,color='#ff4b4b').encode(x='Passo:Q',y='Solicitada:Q',tooltip=['Passo','Dimensão','Motivo',alt.Tooltip('Quantidade solicitada:Q',format=',.0f'),alt.Tooltip('Quantidade executada:Q',format=',.0f'),alt.Tooltip('Quantidade rejeitada:Q',format=',.0f'),alt.Tooltip('Solicitada:Q',title='H solicitado',format='.1%')]),
        ])
    st.altair_chart(alt.layer(*layers).properties(height=350),width='stretch')

def vars_for(t,m):
    sector,factor=st.session_state.sector_meta.get(t,('Outro',1.0))
    return {'ADV':m.adv,'FLOAT':float(m.float_shares or 0),'PRICE':m.price,'TURNOVER':m.turnover_brl,'VOL':m.volatility,'SECTOR':factor}

def h0_for(t,m):
    v=vars_for(t,m)
    g=max(0.,evaluate(st.session_state.h0_gross_expr,v)); p=max(0.,evaluate(st.session_state.h0_plus_expr,v)); n=max(0.,evaluate(st.session_state.h0_minus_expr,v))
    # Structural reachability: gross must dominate either one-way net cap.
    g=max(g,p,n)
    return g,p,n

def h0_table():
    rows=[]
    for t,m in MARKET.items():
        g,p,n=h0_for(t,m); sec,f=st.session_state.sector_meta.get(t,('Outro',1.0))
        rows.append({'Ticker':t,'Setor':sec,'Fator setor':f,'ADV':m.adv,'Preço':m.price,'Free float':m.float_shares,'Vol.':m.volatility,'H₀ gross':g,'H₀ net+':p,'H₀ net−':n})
    return pd.DataFrame(rows)

def current_hrule():
    return HRule(st.session_state.hmax_expr,st.session_state.signal_expr,st.session_state.decay_expr,st.session_state.update_expr,st.session_state.get('sat_kind','hyperbolic'),st.session_state.get('sat_shape',3.0))

def progression(ticker,h0,steps=12,u=.7,reversal_at=0):
    rr=current_hrule(); info=0.; streak=0; rows=[]; direction='BUY'
    params={'I_MULT':st.session_state.get('I_MULT',1.0),'LAMBDA':st.session_state.get('LAMBDA',.15),'GAIN':st.session_state.get('GAIN',.35),'ACCEL':st.session_state.get('ACCEL',.15),'REV_PENALTY':st.session_state.get('REV_PENALTY',.30)}
    for k in range(steps+1):
        variables={'I':info,'U':u,'STREAK':float(streak),'REV':0.,**params}
        h=rr.capacity(h0,variables); hm=rr.hmax(h0,variables); sig=rr.signal(variables); sat=endpoint_saturation(sig,rr.saturation,rr.saturation_shape)
        rows.append({'Passo':k,'H':h,'Hmax':hm,'I':info,'Sinal normalizado':sig,'Saturação':sat,'Direção':direction})
        if k==steps: break
        reverse=(reversal_at>0 and k+1==reversal_at)
        if reverse: direction='SELL' if direction=='BUY' else 'BUY'; streak=1
        else: streak+=1
        info=rr.update_information(info,u,streak,reverse,params)
    return pd.DataFrame(rows)

def opening_capacity(ticker, information=0.0):
    """Resolve the configured data/variables/H chain for a window opening."""
    h0g,h0p,h0m=h0_for_new(ticker)
    params={'I_MULT':st.session_state.get('I_MULT',1.0),'LAMBDA':st.session_state.get('LAMBDA',.15),'GAIN':st.session_state.get('GAIN',.35),'ACCEL':st.session_state.get('ACCEL',.15),'REV_PENALTY':st.session_state.get('REV_PENALTY',.30)}
    variables={**all_vars_for(ticker),'I':float(information),'U':0.0,'STREAK':0.0,'REV':0.0,**params}
    rule=current_hrule()
    gross=rule.capacity(h0g,variables); plus=rule.capacity(h0p,variables); minus=rule.capacity(h0m,variables)
    return (h0g,h0p,h0m),(max(gross,plus,minus),plus,minus)

def observed_treasury(ticker):
    values=all_vars_for(ticker)
    by_name={str(name).casefold():value for name,value in values.items()}
    for candidate in ('treasury','treasury_shares','ações_tesouraria','acoes_tesouraria'):
        value=by_name.get(candidate.casefold())
        if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value)):
            return max(0.0,float(value)),candidate.upper()
    return None,None

def reference_price_for(ticker):
    """Return the configured observed price for a ticker, when usable."""
    if not ticker:
        return None
    field=semantic_mapping('reference_price')
    values=all_vars_for(ticker)
    value=values.get(field) if field else None
    if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value)) and float(value)>0:
        return float(value)
    return None

def experiment_prerequisites(ticker):
    issues=[]
    values=all_vars_for(ticker) if ticker else {}
    if not ticker:
        issues.append('selecione um ticker de referência em **Cenários**')
    if not st.session_state.get('treasury_override_enabled'):
        field=semantic_mapping('treasury')
        if not field or field not in values:
            issues.append('informe em **Variáveis → Mapeamentos semânticos** o campo de ações em tesouraria')
    if st.session_state.get('position_limit_enabled'):
        field=st.session_state.get('position_limit_field')
        if not field or field not in values:
            issues.append('informe em **Especificações → Intrawindow** o campo de referência do limite de posição')
    return issues

def friendly_experiment_error(exc):
    message=str(exc)
    if 'tesouraria' in message.casefold() or 'treasury' in message.casefold():
        return 'Pré-requisito — informe em **Variáveis → Mapeamentos semânticos** o campo de ações em tesouraria.'
    if 'limite de posição' in message.casefold():
        return 'Pré-requisito — informe em **Especificações → Intrawindow** o campo de referência do limite de posição.'
    return 'Não foi possível resolver a especificação: '+_friendly_formula_error(exc)

def resolved_experiment_config(ticker, information=None):
    """Resolve one experiment against the current analytical base."""
    information=float(st.session_state.get('iw_opening_information',0.0) if information is None else information)
    _,capacities=opening_capacity(ticker,information)
    gross,plus,minus=map(float,capacities)
    values=all_vars_for(ticker)
    if st.session_state.get('treasury_override_enabled') and st.session_state.get('treasury_override_explicit',False):
        treasury=float(st.session_state.get('treasury_override',0.0))
    else:
        field=semantic_mapping('treasury')
        if not field or field not in values: raise ValueError('selecione o campo que representa ações em tesouraria')
        treasury=float(values[field])
    minus=min(minus,max(0.,treasury))
    if st.session_state.get('position_limit_enabled'):
        field=st.session_state.get('position_limit_field')
        if not field or field not in values: raise ValueError('selecione o campo de referência do limite de posição')
        ceiling=float(values[field])*float(st.session_state.get('position_limit_ratio',25.0))/100.0
        plus=min(plus,max(0.,ceiling-treasury))
    gross=max(gross,plus,minus)
    policy=next(iter(st.session_state.configs.values()))
    return Config(st.session_state.get('spec_name','Experimento'),gross,plus,minus,policy.rho_gross,policy.rho_plus,policy.rho_minus,treasury)

def resolved_saved_experiment(experiment,ticker,with_trace=False):
    cfg=experiment['config']; capacity=cfg['capacity']; memory=cfg['memory']; iw=cfg['intrawindow']
    values=all_vars_for(ticker)
    h0g=max(0.,evaluate(capacity['h0_gross_expr'],values)); h0p=max(0.,evaluate(capacity['h0_plus_expr'],values)); h0m=max(0.,evaluate(capacity['h0_minus_expr'],values)); h0g=max(h0g,h0p,h0m)
    info=float(cfg.get('opening_information',0.0)); params={key:float(memory.get(key,0.) or 0.) for key in ('I_MULT','LAMBDA','GAIN','ACCEL','REV_PENALTY')}
    variables={**values,'I':info,'U':0.,'STREAK':0.,'REV':0.,**params}
    rule=HRule(capacity['hmax_expr'],memory['signal_expr'],memory['decay_expr'],memory['update_expr'],capacity.get('sat_kind','hyperbolic'),float(capacity.get('sat_shape',3.0)))
    gross=rule.capacity(h0g,variables); plus=rule.capacity(h0p,variables); minus=rule.capacity(h0m,variables)
    calculated={'Gross':float(gross),'Net+':float(plus),'Net−':float(minus)}
    override_active=bool(iw.get('treasury_override_enabled') and iw.get('treasury_override_explicit',False))
    if override_active:
        treasury=float(iw.get('treasury_override',0.0))
        treasury_source='Override experimental'
    else:
        field=semantic_mapping('treasury')
        if not field or field not in values: raise ValueError('campo de Treasury não configurado')
        treasury=float(values[field])
        treasury_source=f'Treasury global · {field}'
    minus=min(minus,max(0.,treasury))
    plus_constraint=None
    if iw.get('position_limit_enabled'):
        field=iw.get('position_limit_field')
        if not field or field not in values: raise ValueError('campo do limite de posição não configurado')
        ceiling=float(values[field])*float(iw.get('position_limit_ratio',25.0))/100.0
        plus_constraint=max(0.,ceiling-treasury)
        plus=min(plus,plus_constraint)
    gross=max(gross,plus,minus)
    config=Config(experiment['name'],gross,plus,minus,float(iw.get('rho_gross',.5)),float(iw.get('rho_plus',.5)),float(iw.get('rho_minus',.5)),treasury)
    trace={
        'Gross':{'calculated':calculated['Gross'],'constraint':None,'source':'H calculado','effective':float(gross)},
        'Net+':{'calculated':calculated['Net+'],'constraint':plus_constraint,'source':'Limite de posição própria' if plus_constraint is not None else 'H calculado','effective':float(plus)},
        'Net−':{'calculated':calculated['Net−'],'constraint':max(0.,treasury),'source':treasury_source,'effective':float(minus)},
    }
    return (config,trace) if with_trace else config



if 'source_specs' not in st.session_state: st.session_state.source_specs=list(_saved.get('source_specs',[]))
if 'source_cache' not in st.session_state: st.session_state.source_cache={}

def snapshot_primitives(m):
    return {'ADV':m.adv,'FLOAT':float(m.float_shares or 0),'PRICE':m.price,'TURNOVER':m.turnover_brl,'VOL':m.volatility}

def source_specs():
    out={}
    for r in st.session_state.source_specs:
        name=str(r.get('Variável','')).strip().upper()
        if not name: continue
        try: tv=json.loads(str(r.get('Template vars','{}') or '{}'))
        except Exception: tv={}
        try: headers=json.loads(str(r.get('Headers','{}') or '{}'))
        except Exception: headers={}
        out[name]=SourceSpec(
            variable=name, provider=str(r.get('Provider','Arquivo local')), unit=str(r.get('Unidade','')),
            endpoint=str(r.get('Endpoint','')), field=str(r.get('Campo','')), scale=float(r.get('Escala',1) or 1),
            manual_value=float(r.get('Manual',0) or 0), template_vars=tv, headers=headers,
            local_file=str(r.get('Arquivo','market_snapshot.json')), collection=str(r.get('Coleção','')),
            identifier_field=str(r.get('Identificador','')), identifier_template=str(r.get('ID template','{ticker}') or '{ticker}'))
    return out

def asset_ids():
    base=st.session_state.get('base_table',pd.DataFrame())
    return base.get('main_id',pd.Series(dtype=str)).astype(str).tolist()

def primitive_names():
    base=visible_base(st.session_state.get('base_table',_initial_base_table()))
    return [str(c).upper() for c in base.columns if str(c).casefold()!='main_id']

def resolved_primitives(main_id, _legacy_market=None):
    """Read observed inputs exclusively from the canonical enriched base."""
    base=visible_base(st.session_state.base_table)
    rows=base.loc[base['main_id'].astype(str)==str(main_id)]
    if rows.empty: raise ValueError(f'`main_id` não encontrado na tabela-base: {main_id}')
    row=rows.iloc[0].to_dict()
    values={str(k).upper():v for k,v in row.items() if str(k).casefold()!='main_id'}
    return values,[]


def _initial_base_table():
    # The asset base starts clean. Only an explicit base operation may create the domain.
    return pd.DataFrame(columns=['main_id','__base_origin__','__base_detail__'])
if 'base_table' not in st.session_state:
    saved_rows=_saved.get('base_table',[])
    st.session_state.base_table=canonical_base_columns(pd.DataFrame(saved_rows)) if saved_rows else _initial_base_table()
if 'base_provenance' not in st.session_state: st.session_state.base_provenance=dict(_saved.get('base_provenance',{}))
if 'rel_selected' not in st.session_state: st.session_state.rel_selected=[]

def _insert_token(expr_key:str, token:str):
    # Called as a widget callback: callbacks run before the next widget tree is instantiated,
    # so mutating the text_input state here is safe in Streamlit.
    st.session_state[expr_key]=st.session_state.get(expr_key,'')+token

def _friendly_reference_error(exc: Exception, expression: str) -> str:
    if not str(expression or '').strip():
        return 'Nenhum identificador definido.'
    msg=str(exc)
    if 'invalid syntax' in msg or 'unexpected EOF' in msg or 'EOF while parsing' in msg:
        return 'Expressão incompleta. Revise campos, funções, parênteses, vírgulas e literais.'
    return f'Não foi possível resolver a expressão: {msg}'

def _friendly_formula_error(exc: Exception) -> str:
    msg=str(exc)
    if 'precisa ser numérica' in msg:
        return f'Dado incompatível com cálculo numérico: {msg}'
    if 'variável desconhecida:' in msg:
        name=msg.split('variável desconhecida:',1)[1].strip()
        return f'A função usa `{name}`, mas esse campo ou variável não está disponível.'
    if 'depende de variável desconhecida:' in msg:
        name,missing=msg.split('depende de variável desconhecida:',1)
        return f'`{name.strip()}` depende de campos que não estão disponíveis: {missing.strip()}.'
    if 'invalid syntax' in msg or 'unexpected EOF' in msg or 'EOF while parsing' in msg:
        return 'A função está incompleta. Revise operadores, funções e parênteses.'
    return msg

def _display_value(value) -> str:
    if value is None or pd.isna(value): return '—'
    if isinstance(value,(int,float)) and not isinstance(value,bool): return f'{value:,.6g}'
    return str(value)


def _compact_button_row(items, *, key_prefix: str, callback, callback_args=lambda x: (x,), help_text=None, sort=False):
    """Render clickable fields as compact wrapping buttons.

    Sizing is intentionally delegated to Streamlit/CSS. Earlier versions tried
    to infer a shared width from label length; that made short and nested field
    names visually inconsistent and also obscured callback behavior. These are
    controls, not a data table, so content-sized buttons are the clearest rule.
    """
    values=list(items)
    if sort:
        values=sorted(values,key=lambda x:str(x).casefold())
    if not values:
        return

    # Streamlit >= 1.50 supports horizontal containers that wrap their children.
    # A content-width button stays comfortably clickable without forcing a grid.
    with st.container(horizontal=True, horizontal_alignment="left"):
        for i,v in enumerate(values):
            label=str(v)
            st.button(
                label,
                key=f'{key_prefix}_{i}_{label}',
                help=help_text,
                width='content',
                on_click=callback,
                args=callback_args(v),
            )


def _render_function_help():
    st.markdown('Campos entram como `[campo]`. Funções são digitadas como fórmulas. Números são escritos sem aspas (`5`); textos usados como argumentos usam aspas (`".SA"`). Literais anexados diretamente podem ser escritos normalmente: `[ticker]:BVMF`.')
    for f,h in FUNCTION_HELP.items():
        st.markdown(f'**{f}** — {h}')
    st.markdown('**Combinando funções**')
    st.caption('As funções podem ser aninhadas livremente. A expressão é avaliada de dentro para fora.')
    st.code('UPPER(TRIM([ticker]))', language=None)
    st.caption('`" petr4 "` → `"PETR4"`')
    st.code('LEFT(5, UPPER(TRIM([symbol])))', language=None)
    st.caption('`" petr4.sa "` → `"PETR4"`')
    st.code('CONCAT(UPPER(TRIM([ticker])), ":BVMF")', language=None)
    st.caption('`" petr4 "` → `"PETR4:BVMF"`')


def _reference_editor(label:str, fields:list[str], key:str, default:str, *, base_identifier:bool=False, show_help:bool=True, scroll_palette:bool=False):
    st.markdown(f'##### {label}')
    if base_identifier:
        st.caption('Defina como esta fonte representa o identificador que alimentará `main_id`. Exemplos: `[key].SA`, `[ticker]:BVMF`, `[ticker]`.')
    else:
        st.caption('As duas referências precisam produzir o mesmo identificador. Modifique uma ou ambas até que os valores coincidam.')
    if key not in st.session_state: st.session_state[key]=default
    st.text_input('Expressão',key=key,label_visibility='collapsed',placeholder='Ex.: [ticker] ou LEFT(5, [symbol])')
    if show_help:
        with st.expander('Funções e sintaxe'):
            _render_function_help()
    st.markdown('**Campos disponíveis nesta referência**')
    palette = st.container(key=f'{key}_palette') if scroll_palette else st.container()
    with palette:
        if fields:
            def _add_field(f): _insert_token(key,f'[{f}]')
            _compact_button_row(fields,key_prefix=f'{key}_field',callback=_add_field)
        else:
            st.caption('Nenhum campo disponível.')
    return st.session_state[key]

@st.dialog('Adicionar fonte à tabela-base',width='large')
def relational_source_dialog():
    kind=st.radio('Tipo de fonte',['Snapshot','API JSON'],horizontal=True)
    base_df=visible_base(st.session_state.base_table)
    if base_df.empty:
        st.warning('Crie a Base de ativos antes de adicionar fontes.'); return
    if kind=='API JSON':
        st.info('A API usa campos já existentes na tabela-base para construir a requisição. O retorno JSON é inspecionado antes de escolher a coleção/campo.')
        endpoint=st.text_input('Endpoint / template',placeholder='https://api.exemplo.com/quote?symbol=[main_id]')
        st.caption('Clique nos campos para copiar a referência e use-a no endpoint; literais são texto normal.')
        cols=st.columns(min(6,len(base_df.columns)))
        for i,c in enumerate(base_df.columns): cols[i%len(cols)].code(f'[{c}]')
        headers=st.text_area('Headers JSON (opcional)',value='{}',height=70)
        unit=st.text_input('Unidade',placeholder='R$')
        test_id=st.selectbox('Registro para testar',base_df['main_id'].astype(str).tolist())
        if st.button('Testar e inspecionar JSON',type='primary'):
            try:
                row=base_df.loc[base_df.main_id.astype(str)==test_id].iloc[0].to_dict()
                url=endpoint
                for c,v in row.items(): url=url.replace(f'[{c}]',str(v))
                from issuer_lab.data_sources import fetch_json
                payload=fetch_json(url,headers=json.loads(headers or '{}'))
                st.session_state.api_preview=payload; st.session_state.api_preview_url=url
                st.success(url)
            except Exception as exc: st.error(str(exc))
        payload=st.session_state.get('api_preview')
        if payload is not None:
            # persist preview in temp JSON so the same inspector is used
            tmp=SOURCES_DIR/'__api_preview__.json'; tmp.write_text(json.dumps(payload),encoding='utf-8')
            info=inspect_snapshot(tmp); opts=[x['path'] for x in info['collections']]
            collection=st.selectbox('Coleção',opts or ['root'])
            rel=load_relation(tmp,collection); fields=[str(c) for c in rel.columns]
            selected=st.selectbox('Campo a adicionar',fields)
            name_col,description_col=st.columns([1,2])
            newname=name_col.text_input('Nome na base',value=str(selected).upper())
            new_description=description_col.text_input('Descrição (opcional)',placeholder='Ex.: ações mantidas em tesouraria')
            if st.button('Adicionar coluna da API',width='stretch'):
                try:
                    name=validate_unique_name(newname,list(base_df.columns))
                    # one request per base row; use same collection and first record for prototype
                    from issuer_lab.data_sources import fetch_json
                    vals=[]
                    for row in base_df.to_dict('records'):
                        url=endpoint
                        for c,v in row.items(): url=url.replace(f'[{c}]',str(v))
                        pl=fetch_json(url,headers=json.loads(headers or '{}')); tmp.write_text(json.dumps(pl),encoding='utf-8')
                        rr=load_relation(tmp,collection)
                        if rr.empty: raise ValueError(f'sem registro para {row["main_id"]}')
                        vals.append(rr.iloc[0][selected])
                    st.session_state.base_table[name]=vals
                    st.session_state.base_provenance[name]={'source':endpoint,'field':selected,'collection':collection,'kind':'API JSON','description':new_description.strip()}
                    st.session_state.api_preview=None; tmp.unlink(missing_ok=True); persist_workspace(); st.rerun()
                except Exception as exc: st.error(str(exc))
        return

    files=discover_local_sources(SOURCES_DIR)
    files=[f for f in files if f!='__api_preview__.json']
    if not files: st.warning('Adicione CSV, XLSX ou JSON em data/sources/.'); return
    def _reset_rel_source():
        st.session_state.rel_src_ref=''
        st.session_state.rel_selected=[]
    file=st.selectbox('Arquivo',files,key='rel_file',on_change=_reset_rel_source)
    info=inspect_snapshot(SOURCES_DIR/file)
    st.caption(f'Formato detectado: **{info["format"]}**')
    opts=[x['path'] for x in info['collections']]
    collection=st.selectbox('Coleção',opts,index=0,key='rel_collection',on_change=_reset_rel_source,help='Para JSON nested, escolha a coleção detectada. `root` significa que a própria raiz já é a relação.')
    meta=next(x for x in info['collections'] if x['path']==collection)
    st.caption(f'{meta["count"]} registros · {len(meta["fields"])} campos')
    header_row=0
    if info["format"] in {"CSV","XLSX"}:
        candidates=header_candidates(SOURCES_DIR/file,collection)
        suggested=suggested_header_row(SOURCES_DIR/file,collection)
        rows=sorted({x['row'] for x in candidates})
        header_row=st.selectbox('Linha de cabeçalho',rows,index=rows.index(suggested) if suggested in rows else 0,format_func=lambda x:f'Linha {x+1}',help='Use isto para ignorar títulos/notas antes da tabela real.')
        with st.expander('Inspecionar linhas candidatas'):
            st.dataframe(pd.DataFrame(candidates).sort_values('row')[['row','preview']].head(10),hide_index=True,width='stretch',column_config={'row':'linha','preview':'conteúdo detectado'})
    src=load_relation(SOURCES_DIR/file,collection,header_row=header_row)
    st.markdown('**5 primeiros resultados da fonte**')
    st.dataframe(src.head(5),hide_index=True,width='stretch')
    st.markdown('#### Correspondência entre base e fonte')
    st.caption('A referência da tabela-base e a referência da fonte precisam produzir o **mesmo identificador**. Ajuste as expressões até que os valores coincidam.')
    with st.expander('Funções e sintaxe'):
        _render_function_help()
    rb,rs=st.columns(2,gap='small')
    with rb:
        base_ref=_reference_editor('Referência da tabela-base',list(base_df.columns),'rel_base_ref','[main_id]',show_help=False,scroll_palette=True)
    with rs:
        src_ref=_reference_editor('Referência da fonte',list(src.columns),'rel_src_ref','',show_help=False,scroll_palette=True)
    if not base_ref.strip() or not src_ref.strip():
        st.info('Nenhum identificador definido.' if not src_ref.strip() else 'Defina as duas referências para validar a correspondência.')
    else:
        try:
            source_ref_values=[eval_reference(src_ref,r) for r in src.to_dict('records')]
            source_ref_set=set(source_ref_values)
            base_ref_values=[eval_reference(base_ref,r) for r in base_df.to_dict('records')]
            base_ref_set=set(base_ref_values)

            # The preview is anchored on the base because the base defines the experiment universe.
            preview=[]
            for i,(row,ref_value) in enumerate(zip(base_df.head(5).to_dict('records'),base_ref_values[:5])):
                found=ref_value in source_ref_set
                preview.append({
                    'main_id': str(row.get('main_id','')),
                    'Referência da base': ref_value,
                    'Referência na fonte': ref_value if found else '—',
                    'Status': '✓ Correspondência encontrada' if found else '✕ Sem correspondência',
                })
            st.markdown('##### 5 primeiras correspondências')
            st.dataframe(pd.DataFrame(preview),hide_index=True,width='stretch')

            matched=sum(x in source_ref_set for x in base_ref_values)
            total=len(base_ref_values)
            pct=(100.0*matched/total) if total else 0.0
            if matched==total:
                st.success(f'✓ {matched} / {total} correspondências · {pct:.0f}%')
            elif matched==0:
                st.error(f'✕ {matched} / {total} correspondências · {pct:.0f}%')
            else:
                st.warning(f'{matched} / {total} correspondências · {pct:.0f}%')

            missing_in_source=[str(base_df.iloc[i]['main_id']) for i,x in enumerate(base_ref_values) if x not in source_ref_set]
            source_outside_base=[]
            seen=set()
            for x in source_ref_values:
                if x not in base_ref_set and x not in seen:
                    source_outside_base.append(str(x)); seen.add(x)
            if missing_in_source or source_outside_base:
                with st.expander('Detalhes da correspondência'):
                    st.markdown('**Na base, sem correspondência na fonte**')
                    st.write(', '.join(missing_in_source) if missing_in_source else 'Nenhum.')
                    st.markdown('**Na fonte, fora da base**')
                    st.write(', '.join(source_outside_base) if source_outside_base else 'Nenhum.')
                    st.caption('O primeiro caso produz informação ausente para ativos do experimento. O segundo é ignorado pela interseção e não cria novos `main_id`.')
        except Exception as exc:
            st.info(_friendly_reference_error(exc,(base_ref or '')+(src_ref or '')))
    st.markdown('##### Campos a agregar')
    selected=st.session_state.rel_selected
    available=[c for c in src.columns if c not in selected]
    def _select_rel(c):
        if c not in st.session_state.rel_selected: st.session_state.rel_selected.append(c)
    def _unselect_rel(c):
        if c in st.session_state.rel_selected: st.session_state.rel_selected.remove(c)
    st.markdown('**Selecionáveis**')
    if available:
        _compact_button_row(available,key_prefix=f'av_{file}_{collection}',callback=_select_rel,callback_args=lambda c:(c,))
    else: st.caption('—')
    st.markdown('**Selecionados**')
    if selected:
        _compact_button_row(list(selected),key_prefix=f'sel_{file}_{collection}',callback=_unselect_rel,callback_args=lambda c:(c,))
    else: st.caption('—')
    if selected:
        # Preview the exact join that will be persisted. Temporary destination
        # names must already follow join_snapshot's uppercase normalization;
        # otherwise looking them up afterwards can raise a misleading KeyError.
        try:
            occupied={str(c).casefold() for c in base_df.columns}
            preview_names={}
            for i,c in enumerate(selected):
                candidate=f'_PREVIEW_COLUMN_{i}'
                while candidate.casefold() in occupied:
                    candidate=f'_{candidate}'
                preview_names[c]=candidate
                occupied.add(candidate.casefold())
            joined_preview,_=join_snapshot(base_df,src,base_ref,src_ref,preview_names)
            existing=list(base_df.columns)
            if len(existing)>3:
                pv=pd.DataFrame(index=joined_preview.head(5).index)
                pv[existing[0]]=joined_preview[existing[0]].head(5)
                pv[existing[1]]=joined_preview[existing[1]].head(5)
                pv['[...]']='…'
                pv[existing[-1]]=joined_preview[existing[-1]].head(5)
            else:
                pv=joined_preview[existing].head(5).copy()
            for c in selected:
                pv[f'➕ {c}']=joined_preview[preview_names[c]].head(5).values
            st.markdown('##### 5 primeiros resultados da tabela-base')
            st.dataframe(pv,hide_index=True,width='stretch')
        except Exception as exc:
            st.info(_friendly_reference_error(exc, (base_ref or '') + (src_ref or '')))
    names={}; descriptions={}
    if selected:
        st.markdown('##### Nomes na tabela-base')
        st.caption('Defina o nome técnico e, opcionalmente, o significado econômico ou operacional de cada campo.')
        for c in selected:
            st.markdown(f'**{c}**')
            name_col,description_col=st.columns([1,2])
            names[c]=name_col.text_input('Nome',value=str(c).upper(),key=f'name_{file}_{collection}_{c}',label_visibility='collapsed',placeholder='Nome na tabela-base')
            descriptions[c]=description_col.text_input('Descrição',key=f'description_{file}_{collection}_{c}',label_visibility='collapsed',placeholder='Descrição opcional')
    if st.button('Adicionar à tabela-base',type='primary',width='stretch',disabled=not bool(selected)):
        try:
            # validate all names before mutation, case-insensitive
            seen=list(base_df.columns); clean={}
            for c in selected:
                n=validate_unique_name(names[c],seen); seen.append(n); clean[c]=n
            out,stats=join_snapshot(base_df,src,base_ref,src_ref,clean)
            meta=st.session_state.base_table[['main_id','__base_origin__','__base_detail__']].copy()
            st.session_state.base_table=meta.merge(out,on='main_id',how='left')
            for c,n in clean.items(): st.session_state.base_provenance[n]={'source':file,'collection':collection,'field':c,'base_reference':base_ref,'source_reference':src_ref,'kind':'Snapshot','description':descriptions[c].strip()}
            st.session_state.rel_selected=[]; persist_workspace(); st.success(f'{stats["matched"]}/{stats["total"]} referências encontradas'); st.rerun()
        except Exception as exc: st.error(str(exc))

@st.dialog("Ajuda · Issuer Protocol Lab", width="large")
def help_dialog():
    st.markdown("""**Primeiros passos**

O Lab separa **dados observados → conceitos construídos → estados → capacidade H → execução → auditoria**. Os números padrão são experimentais, não calibração regulatória.

**Conectar dados externos**

Em **Dados → Configurar fonte**, escolha **API JSON**, **Arquivo local** ou **Manual**.

- **API JSON:** `{ticker}` é fornecido automaticamente para cada ativo. O endpoint pode usar `{ticker}` e constantes opcionais do provider. Use **Testar fonte** antes de salvar.
- **Arquivo local:** coloque `.csv` ou `.json` em `data/sources/`. O Lab descobre os arquivos automaticamente e inspeciona colunas/estrutura. Você não digita caminhos.
- **Identificação:** o template combina variáveis e separadores livremente, por exemplo `{ticker}`, `{ticker}.SA`, `BVMF:{ticker}`. Para CSV/listas JSON, escolha também o campo identificador; para mapas JSON indexados pelo ticker, deixe-o vazio.
- **Campo de valor:** em CSV é escolhido entre as colunas. Em JSON pode ser um caminho como `metrics.avg_daily_volume_shares`.

**Variáveis** podem depender de primitivas ou de outras variáveis. **H** consome essas variáveis/estados. **Auditoria** reconstrói a cadeia causal.

O protótipo suporta GET/JSON, CSV/JSON local e entrada manual. OAuth, POST e paginação ficam fora do escopo desta versão.""")

def _id_builder(default='{ticker}', key='idb'):
    st.markdown('##### Identificação')
    st.caption('Monte o identificador com variáveis e separadores. `{ticker}` vem do ativo atual; demais placeholders podem ser constantes do provider.')
    template=st.text_input('Template do identificador',value=default or '{ticker}',key=f'{key}_text',placeholder='{ticker}.SA')
    tokens=['{ticker}','{region}','{exchange}','{suffix}','.',':','/','-','_']
    cols=st.columns(len(tokens))
    for c,tok in zip(cols,tokens):
        if c.button(tok,key=f'{key}_{tok}'):
            st.session_state[f'{key}_text']=st.session_state.get(f'{key}_text','')+tok
            st.rerun()
    st.caption('Blocos rápidos para composição; o campo continua livre para qualquer literal ou placeholder.')
    return template

@st.dialog("Configurar fonte de dados", width="large")
def source_dialog():
    existing=["— nova variável —"]+[str(r.get("Variável","")) for r in st.session_state.source_specs if r.get("Variável")]
    pick=st.selectbox("Variável",existing,key="src_pick")
    base={} if pick=="— nova variável —" else next((r for r in st.session_state.source_specs if r.get("Variável")==pick),{})
    variable=st.text_input("Nome da variável",value="" if pick=="— nova variável —" else pick,placeholder="MARKET_CAP")
    c1,c2=st.columns(2)
    providers=["API JSON","Arquivo local","Manual"]
    current=base.get("Provider","API JSON")
    if current=='Snapshot local': current='Arquivo local'
    provider=c1.selectbox("Provider",providers,index=providers.index(current) if current in providers else 0)
    unit=c2.text_input("Unidade",value=str(base.get("Unidade","")),placeholder="R$")
    endpoint=''; tv='{}'; headers='{}'; local_file=''; collection=''; identifier=''; id_template='{ticker}'; field=''; scale=1.; manual=float(base.get('Manual',0) or 0)

    if provider=='API JSON':
        endpoint=st.text_input("Endpoint",value=str(base.get("Endpoint","")),placeholder="https://api.exemplo.com/quote?symbol={ticker}")
        id_template=_id_builder(str(base.get('ID template','{ticker}') or '{ticker}'),'api_id')
        tv=st.text_area("Constantes do provider (JSON, opcional)",value=str(base.get("Template vars","{}") or "{}"),placeholder='{"suffix":"SA"}',height=75)
        st.caption('O endpoint pode usar `{ticker}` diretamente. O identificador acima documenta/valida a convenção do provider; constantes existem apenas quando a fonte realmente as exige.')
        headers=st.text_area("Headers (JSON, opcional)",value=str(base.get("Headers","{}") or "{}"),placeholder='{"Authorization":"Bearer SEU_TOKEN"}',height=75)
        c3,c4=st.columns(2)
        field=c3.text_input("Campo JSON",value=str(base.get("Campo","")),placeholder="results.0.data.marketCap")
        scale=c4.number_input("Escala",value=float(base.get("Escala",1) or 1),format="%.6g")
    elif provider=='Arquivo local':
        files=discover_local_sources(SOURCES_DIR)
        if not files:
            st.warning('Nenhum .csv/.json em data/sources/. Adicione um arquivo e reabra este modal.')
        else:
            current_file=str(base.get('Arquivo','market_snapshot.json'))
            idx=files.index(current_file) if current_file in files else 0
            local_file=st.selectbox('Arquivo',files,index=idx)
            info=inspect_local_source(SOURCES_DIR/local_file)
            st.caption(f'Formato detectado: **{info["format"]}** · arquivo descoberto automaticamente em `data/sources/`.')
            if info['format']=='CSV':
                cols=info.get('columns',[])
                a,b=st.columns(2)
                identifier=a.selectbox('Campo identificador',cols,index=cols.index(str(base.get('Identificador','ticker'))) if str(base.get('Identificador','ticker')) in cols else 0)
                field=b.selectbox('Campo de valor',cols,index=cols.index(str(base.get('Campo',''))) if str(base.get('Campo','')) in cols else 0)
                id_template=_id_builder(str(base.get('ID template','{ticker}') or '{ticker}'),'csv_id')
                with st.expander('Prévia do arquivo'): st.dataframe(pd.DataFrame(info['preview']),hide_index=True,width='stretch')
            else:
                collections=['— raiz —']+info.get('collections',[])
                old=str(base.get('Coleção',''))
                ci=collections.index(old) if old in collections else (collections.index('tickers') if 'tickers' in collections else 0)
                choice=st.selectbox('Coleção de registros',collections,index=ci)
                collection='' if choice=='— raiz —' else choice
                st.caption('Se a coleção for um mapa indexado pelo ticker, deixe **Campo identificador** vazio. Se for uma lista de registros, informe o caminho do identificador, ex. `symbol`.')
                a,b=st.columns(2)
                identifier=a.text_input('Campo identificador (opcional)',value=str(base.get('Identificador','')),placeholder='symbol')
                field=b.text_input('Campo de valor',value=str(base.get('Campo','')),placeholder='metrics.avg_daily_volume_shares')
                id_template=_id_builder(str(base.get('ID template','{ticker}') or '{ticker}'),'json_id')
                with st.expander('Estrutura / prévia JSON'): st.json(info['preview'])
            scale=st.number_input('Escala',value=float(base.get('Escala',1) or 1),format='%.6g')
    else:
        manual=st.number_input("Valor manual",value=float(base.get("Manual",0) or 0),format="%.6g")
        scale=st.number_input("Escala",value=float(base.get("Escala",1) or 1),format="%.6g")

    st.markdown("##### Teste da fonte")
    test_tickers=st.multiselect("Tickers de teste",["PETR4","VALE3","BBSE3","MGLU3","KEPL3"],default=["PETR4","VALE3","BBSE3","MGLU3","KEPL3"],help="Conjunto heterogêneo: 2 blue chips, 2 intermediárias e 1 ação menor. Em APIs, a última pode expor imediatamente necessidade de autenticação/cobertura.")
    if st.button("Testar fonte",type="primary"):
        try:
            tv_obj=json.loads(tv or "{}"); hdr_obj=json.loads(headers or "{}")
            spec=SourceSpec(variable.strip().upper() or "TEST",provider,unit,endpoint,field,float(scale),float(manual),tv_obj,hdr_obj,local_file,collection,identifier,id_template)
            for ticker in test_tickers:
                try:
                    if provider=='API JSON':
                        result=test_api_source(spec,ticker); st.success(f'{ticker} · OK · {result["value"]:,.6g} {unit} · {result["url"]}')
                        with st.expander(f"JSON · {ticker}"): st.json(result["payload"])
                    elif provider=='Arquivo local':
                        result=test_local_source(spec,ticker,SOURCES_DIR); st.success(f'{ticker} · OK · {result["value"]:,.6g} {unit} · {local_file}')
                        with st.expander(f'Registro · {ticker}'): st.json(result['record'])
                    else: st.success(f'{ticker} · OK · {float(manual)*float(scale):,.6g} {unit} · entrada manual')
                except Exception as exc: st.error(f"{ticker} · {exc}")
        except Exception as exc: st.error(f"Configuração inválida: {exc}")
    if st.button("Salvar fonte",width="stretch"):
        try:
            if not variable.strip(): raise ValueError("informe o nome da variável")
            json.loads(tv or "{}"); json.loads(headers or "{}")
            row={"Variável":variable.strip().upper(),"Provider":provider,"Unidade":unit,"Endpoint":endpoint,"Arquivo":local_file,"Coleção":collection,"Identificador":identifier,"ID template":id_template,"Campo":field,"Escala":float(scale),"Manual":float(manual),"Template vars":tv or "{}","Headers":headers or "{}"}
            rows=[r for r in st.session_state.source_specs if str(r.get("Variável","")).upper()!=row["Variável"]]
            rows.append(row); st.session_state.source_specs=rows; st.session_state.source_cache={}; persist_workspace(); st.rerun()
        except Exception as exc: st.error(str(exc))

_title,_undo,_redo,_help=st.columns([10,1,1,1])
with _title: st.title("Issuer Protocol Lab")
_scope='foundation' if st.session_state.get('main_nav','Dados') in ('Dados','Variáveis') else ('scenario' if st.session_state.get('main_nav')=='Cenários' else 'experiment')
_undo_count,_redo_count=history_status(st.session_state._project,_scope)
with _undo:
    st.write("")
    if st.button("↶",key="global_undo",help=f"Desfazer neste contexto ({_undo_count} disponíveis)",width="stretch"):
        if not undo(st.session_state._project,_scope): st.toast('Não há alterações para desfazer neste contexto.')
        else:
            save_project(WORKSPACE_FILE,st.session_state._project)
            project=st.session_state._project
            st.session_state.clear(); st.session_state._pending_project=project; st.session_state._restore_notice='Alteração desfeita.'; st.rerun()
with _redo:
    st.write("")
    if st.button("↷",key="global_redo",help=f"Refazer neste contexto ({_redo_count} disponíveis)",width="stretch"):
        if not redo(st.session_state._project,_scope): st.toast('Não há alterações para refazer neste contexto.')
        else:
            save_project(WORKSPACE_FILE,st.session_state._project)
            project=st.session_state._project
            st.session_state.clear(); st.session_state._pending_project=project; st.session_state._restore_notice='Alteração refeita.'; st.rerun()
with _help:
    st.write("")
    if st.button("?",key="global_help",help="Instruções de uso",type="secondary",width="stretch"): help_dialog()
st.markdown('<div class="muted">Laboratório de especificação, dinâmica e auditoria do protocolo de negociação da companhia.</div>',unsafe_allow_html=True)
TAB_GUIDE={'Dados':'O que sabemos?','Variáveis':'Como transformamos dados em conceitos econômicos?','Cenários':'Que ordens a companhia envia ao mercado?','Memória':'Como estados informacionais evoluem?','Capacidade':'Como o estado determina H e sua progressão?','Intrawindow':'O que acontece dentro de uma janela?','Especificações':'Quais regras definem o protocolo?','Comparar':'Como cenários e especificações se comportam em conjunto?','Auditoria':'Por que aconteceu esse resultado?'}
st.markdown(r'''<style>
/* Navegação persistente: um único widget é a fonte de verdade. */
.st-key-main_nav [data-testid="stWidgetLabel"]{display:none!important}
.st-key-main_nav [role="radiogroup"]{display:flex!important;gap:.25rem!important;align-items:stretch!important;flex-wrap:wrap!important;border-bottom:1px solid rgba(128,128,128,.28);padding-bottom:.15rem}
.st-key-main_nav label{position:relative!important;min-width:92px!important;min-height:42px!important;padding:.55rem .8rem!important;margin:0!important;display:flex!important;align-items:center!important;justify-content:center!important;border-radius:8px 8px 0 0!important}
.st-key-main_nav label p{font-size:.93rem!important;font-weight:650!important;white-space:nowrap!important;margin:0!important}
.st-key-main_nav label:has(input:checked){background:rgba(255,75,75,.10)!important;border-bottom:2px solid #ff4b4b!important}
.st-key-main_nav label:has(input:checked) p{color:#ff4b4b!important}
.st-key-main_nav label:hover{background:rgba(128,128,128,.10)!important}
.st-key-main_nav label:hover::after{position:absolute;top:calc(100% + 7px);left:50%;transform:translateX(-50%);z-index:99999;padding:.42rem .62rem;border:1px solid rgba(128,128,128,.35);border-radius:.45rem;background:#171b22;color:#f2f4f8;font-size:.76rem;font-weight:500;white-space:nowrap;box-shadow:0 4px 16px rgba(0,0,0,.25);pointer-events:none}
.st-key-main_nav label:nth-child(1):hover::after{content:"O que sabemos?"}
.st-key-main_nav label:nth-child(2):hover::after{content:"Como transformamos dados em conceitos econômicos?"}
.st-key-main_nav label:nth-child(3):hover::after{content:"Trajetórias de ordens por companhia e estratégia"}
.st-key-main_nav label:nth-child(4):hover::after{content:"Regras de memória, capacidade e intrawindow"}
.st-key-main_nav label:nth-child(5):hover::after{content:"Comparação entre especificações e cenários"}
</style>''',unsafe_allow_html=True)
NAV_PAGES=['Dados','Variáveis','Cenários','Especificações','Comparar']
if st.session_state.get('main_nav') not in NAV_PAGES:
    st.session_state.main_nav='Dados'
# A única fonte de verdade para navegação. Isso preserva a página selecionada em reruns de widgets.
page=st.radio('Navegação',NAV_PAGES,horizontal=True,label_visibility='collapsed',key='main_nav')
experiment_section=None
if page=='Especificações' and active_draft(st.session_state._project):
    sections=['Visão geral','Memória','Capacidade','Intrawindow','Gerenciar']
    saved_section=st.session_state._project.get('ui',{}).get('experiment_section','Visão geral')
    if st.session_state.get('experiment_section') not in sections: st.session_state.experiment_section=saved_section if saved_section in sections else 'Visão geral'
    experiment_section=st.radio('Área da especificação',sections,horizontal=True,key='experiment_section')
def tab_intro(name):
    st.markdown(f'**{TAB_GUIDE[name]}**')
    st.caption({'Dados':'Snapshot e proveniência dos dados primitivos disponíveis ao modelo.','Variáveis':'Variáveis derivadas podem depender de dados primitivos ou de outras variáveis derivadas.','Cenários':'Trajetórias exógenas e reutilizáveis, identificadas por companhia e estratégia.','Memória':'Sinal, atualização e decay são relações independentes e editáveis.','Capacidade':'H₀, Hmax, resposta ao estado e trajetória entre janelas no mesmo contexto.','Intrawindow':'Q gera alerta intraday; a obrigação de disclosure é avaliada no fechamento. H permanece o hard cap.','Especificações':'Regras formais de Memória, Capacidade e Intrawindow.','Comparar':'Análise de uma ou várias combinações entre especificações e cenários.','Auditoria':'Reconstrução causal da trajetória a partir de regras, estado e eventos.'}[name])
PRIMITIVE_HELP={}
if 'derived_defs' not in st.session_state:
    st.session_state.derived_defs=list(_saved.get('derived_defs',[]))
def derived_descriptions():
    out={}
    for row in st.session_state.derived_defs:
        name=str(row.get('Nome','')).strip().upper()
        desc=str(row.get('Descrição','')).strip()
        if name: out[name]=desc or 'conceito intermediário sem descrição'
    return out

def derived_map():
    defs={}
    for row in st.session_state.derived_defs:
        name=str(row.get('Nome','')).strip().upper(); expr=str(row.get('Função','')).strip()
        if name and expr: defs[name]=expr
    return defs
def all_vars_for(t,m=None):
    base,_=resolved_primitives(t)
    return evaluate_derived(derived_map(),base)
def h0_for_new(t,m=None):
    required={'H₀ gross':st.session_state.h0_gross_expr,'H₀ net+':st.session_state.h0_plus_expr,'H₀ net−':st.session_state.h0_minus_expr}
    missing=[name for name,expr in required.items() if not str(expr).strip()]
    if missing: raise ValueError('configure '+', '.join(missing))
    v=all_vars_for(t); g=max(0.,evaluate(st.session_state.h0_gross_expr,v)); p=max(0.,evaluate(st.session_state.h0_plus_expr,v)); n=max(0.,evaluate(st.session_state.h0_minus_expr,v)); return max(g,p,n),p,n

def build_specification():
    st.session_state.base_table=canonical_base_columns(st.session_state.base_table)
    configs={name:{'h_gross':c.h_gross,'h_plus':c.h_plus,'h_minus':c.h_minus,'rho_gross':c.rho_gross,'rho_plus':c.rho_plus,'rho_minus':c.rho_minus,'treasury':c.treasury} for name,c in st.session_state.configs.items()}
    return LabSpecification(
        name=st.session_state.get('spec_name','Working specification'),
        data={
            'base_table':json.loads(st.session_state.base_table.to_json(orient='records',date_format='iso')),
            'base_provenance':dict(st.session_state.base_provenance),
        },
        derived_defs=list(st.session_state.derived_defs),
        memory={'signal_expr':st.session_state.signal_expr,'update_expr':st.session_state.update_expr,'decay_expr':st.session_state.decay_expr,'I_MULT':st.session_state.get('I_MULT',1.0),'GAIN':st.session_state.get('GAIN',.35),'LAMBDA':st.session_state.get('LAMBDA',.15),'ACCEL':st.session_state.get('ACCEL',.15),'REV_PENALTY':st.session_state.get('REV_PENALTY',.30)},
        capacity={'h0_gross_expr':st.session_state.h0_gross_expr,'h0_plus_expr':st.session_state.h0_plus_expr,'h0_minus_expr':st.session_state.h0_minus_expr,'hmax_expr':st.session_state.hmax_expr,'sat_kind':st.session_state.get('sat_kind','hyperbolic'),'sat_shape':st.session_state.get('sat_shape',3.0)},
        intrawindow={'configs':configs,'active':st.session_state.get('iw_config','Baseline')},
        actions=list(st.session_state.actions),
    )

def apply_specification(spec):
    st.session_state.spec_name=spec.name
    rows=list(spec.data.get('base_table',[]))
    st.session_state.base_table=canonical_base_columns(pd.DataFrame(rows)) if rows else _initial_base_table()
    for col in ['main_id','__base_origin__','__base_detail__']:
        if col not in st.session_state.base_table.columns: st.session_state.base_table[col]=''
    st.session_state.base_provenance=dict(spec.data.get('base_provenance',{}))
    st.session_state.derived_defs=spec.derived_defs
    for k,v in spec.memory.items(): st.session_state[k]=v
    for k,v in spec.capacity.items(): st.session_state[k]=v
    configs={}
    for name,c in spec.intrawindow.get('configs',{}).items(): configs[name]=Config(name,**c)
    if configs: st.session_state.configs=configs
    st.session_state.iw_config=spec.intrawindow.get('active',next(iter(configs), 'Baseline'))
    st.session_state.actions=spec.actions
    st.session_state.source_cache={}

def workspace_payload():
    st.session_state.base_table=canonical_base_columns(st.session_state.base_table)
    configs={name:{'h_gross':c.h_gross,'h_plus':c.h_plus,'h_minus':c.h_minus,'rho_gross':c.rho_gross,'rho_plus':c.rho_plus,'rho_minus':c.rho_minus,'treasury':c.treasury} for name,c in st.session_state.configs.items()}
    return {
        'base_table':json.loads(st.session_state.base_table.to_json(orient='records',date_format='iso')),
        'base_provenance':dict(st.session_state.base_provenance),
        'derived_defs':list(st.session_state.derived_defs),
        'semantic_mappings':dict(st.session_state.get('semantic_mappings',{})),
        'h0_gross_expr':st.session_state.h0_gross_expr,'h0_plus_expr':st.session_state.h0_plus_expr,'h0_minus_expr':st.session_state.h0_minus_expr,
        'hmax_expr':st.session_state.hmax_expr,'signal_expr':st.session_state.signal_expr,'decay_expr':st.session_state.decay_expr,'update_expr':st.session_state.update_expr,
        'GAIN':st.session_state.get('GAIN',.35),'LAMBDA':st.session_state.get('LAMBDA',.15),'ACCEL':st.session_state.get('ACCEL',.15),'REV_PENALTY':st.session_state.get('REV_PENALTY',.30),'I_MULT':st.session_state.get('I_MULT',1.0),
        'sat_kind':st.session_state.get('sat_kind','hyperbolic'),'sat_shape':st.session_state.get('sat_shape',3.0),
        'configs':configs,'actions':list(st.session_state.actions),'source_specs':list(st.session_state.source_specs),'spec_name':st.session_state.get('spec_name','Working specification'),
        'main_nav':st.session_state.get('main_nav','Dados'),
        'iw_ticker':st.session_state.get('iw_ticker'),'iw_opening_information':st.session_state.get('iw_opening_information',0.0),
        'iw_config':st.session_state.get('iw_config','Baseline'),
        'exp_ticker':st.session_state.get('exp_ticker'),'exp_information':st.session_state.get('exp_information',0.0),'exp_config':st.session_state.get('exp_config','Baseline'),
    }

def foundation_payload():
    st.session_state.base_table=canonical_base_columns(st.session_state.base_table)
    mappings=dict(st.session_state.get('semantic_mappings',{}))
    return {
        'base_table':json.loads(st.session_state.base_table.to_json(orient='records',date_format='iso')),
        'base_provenance':dict(st.session_state.base_provenance),
        'derived_defs':list(st.session_state.derived_defs),
        'source_specs':list(st.session_state.source_specs),
        'semantic_mappings':mappings,
    }

def experiment_payload():
    config=next(iter(st.session_state.configs.values()),Config('Experimento',0.,0.,0.,.5,.5,.5,0.))
    return {
        'memory':{key:st.session_state.get(key) for key in ('signal_expr','update_expr','decay_expr','I_MULT','GAIN','LAMBDA','ACCEL','REV_PENALTY')},
        'capacity':{key:st.session_state.get(key) for key in ('h0_gross_expr','h0_plus_expr','h0_minus_expr','hmax_expr','sat_kind','sat_shape')},
        'intrawindow':{
            'rho_gross':float(config.rho_gross),'rho_plus':float(config.rho_plus),'rho_minus':float(config.rho_minus),
            'treasury_override_enabled':bool(st.session_state.get('treasury_override_enabled',False)),
            'treasury_override_explicit':bool(st.session_state.get('treasury_override_explicit',False)),
            'treasury_override':float(st.session_state.get('treasury_override',0.0) or 0.0),
            'position_limit_enabled':bool(st.session_state.get('position_limit_enabled',False)),
            'position_limit_ratio':float(st.session_state.get('position_limit_ratio',25.0) or 25.0),
            'position_limit_field':st.session_state.get('position_limit_field'),
            'topology':'calendar',
        },
        'opening_information':float(st.session_state.get('iw_opening_information',0.0)),
    }

def serializable_result(result):
    if not result: return None
    window=result.get('final_window')
    return {
        'trajectory':result['trajectory'].to_dict('records'),
        'audit':result['audit'].to_dict('records'),
        'events':result['events'].to_dict('records'),
        'checks':result['checks'].to_dict('records'),
        'error':result.get('error'),'capacity_notices':result.get('capacity_notices',[]),'disclosure':result.get('disclosure',[]),
        'capacity_resolution':result.get('capacity_resolution',{}),
        'final':{'gross':window.gross,'net':window.net,'buy':window.buy,'sell':window.sell} if window else {},
        'meta':dict(st.session_state.get('experiment_run_meta',{})),
    }

def persist_workspace():
    project=st.session_state._project
    commit_foundation(project,foundation_payload())
    if active_draft(project):
        commit_active_experiment(project,st.session_state.get('spec_name','Experimento'),experiment_payload())
    scenario_widget_keys=('scenario_company_widget','scenario_strategy_widget','scenario_description_widget')
    if active_scenario(project) and all(key in st.session_state for key in scenario_widget_keys):
        commit_active_scenario(project,str(st.session_state.get('scenario_company_widget') or ''),str(st.session_state.get('scenario_strategy_widget') or ''),str(st.session_state.get('scenario_description_widget') or ''),list(st.session_state.get('actions',[])))
    project.setdefault('ui',{})['main_nav']=st.session_state.get('main_nav','Dados')
    project['ui']['experiment_section']=st.session_state.get('experiment_section','Visão geral')
    for key in ('comparison_mode','comparison_fixed_scenario_id','comparison_fixed_experiment_id','comparison_selected_experiment_ids','comparison_selected_scenario_ids'):
        if key in st.session_state: project['ui'][key]=deepcopy(st.session_state[key])
    save_project(WORKSPACE_FILE,project)

def persist_semantic_mappings(changed_role=None):
    mappings=dict(st.session_state.get('semantic_mappings',{}))
    widget_key={'treasury':'semantic_treasury_widget','reference_price':'semantic_reference_price_widget'}[changed_role]
    other_role='reference_price' if changed_role=='treasury' else 'treasury'
    other_widget='semantic_reference_price_widget' if changed_role=='treasury' else 'semantic_treasury_widget'
    mappings[changed_role]=st.session_state.get(widget_key)
    if mappings[changed_role] is not None and mappings[changed_role]==mappings.get(other_role):
        mappings[other_role]=None
        st.session_state[other_widget]=None
    st.session_state.semantic_mappings=mappings
    project=st.session_state._project
    foundation_state=deepcopy(project.get('foundation',{}).get('state',{}))
    foundation_state['semantic_mappings']=deepcopy(mappings)
    commit_foundation(project,foundation_state)
    changed=adopt_global_treasury_mapping(project)
    if changed and active_draft(st.session_state._project):
        st.session_state.treasury_override_enabled=False
        st.session_state.treasury_override_explicit=False
    save_project(WORKSPACE_FILE,project)
    st.toast('Mapeamentos semânticos salvos.')

def reload_project(project,notice=None):
    save_project(WORKSPACE_FILE,project)
    st.session_state.clear(); st.session_state._pending_project=project
    if notice: st.session_state._restore_notice=notice
    st.rerun()

def primitive_descriptions():
    out={}
    for name in primitive_names():
        p=st.session_state.base_provenance.get(name,{})
        out[name]=provenance_description(p)
    return out

def primitive_metadata_rows():
    rows=[]
    for name in primitive_names():
        p=st.session_state.base_provenance.get(name,{})
        source=str(p.get('source','tabela-base'))
        field=str(p.get('field','') or '')
        rows.append({
            'Campo':name,
            'Fonte':source + (f' · {field}' if field and field.casefold()!=name.casefold() else ''),
            'Descrição':str(p.get('description','') or '').strip(),
        })
    return rows

@st.dialog('Revisar dado observado')
def primitive_description_dialog(field_name):
    provenance=st.session_state.base_provenance.setdefault(field_name,{})
    description=st.text_area(
        'Descrição',value=str(provenance.get('description','') or ''),
        placeholder='O que este dado observado representa?',
        key=f'primitive_description_{field_name}',
    )
    current_role=('Ações em tesouraria' if semantic_mapping('treasury')==field_name else
                  'Preço de referência' if semantic_mapping('reference_price')==field_name else 'Nenhum')
    semantic_role=st.selectbox(
        'Papel semântico', ['Nenhum','Ações em tesouraria','Preço de referência'],
        index=['Nenhum','Ações em tesouraria','Preço de referência'].index(current_role),
        key=f'primitive_semantic_role_{field_name}',
        help='Opcional. Vincula esta coluna diretamente às regras que consomem Treasury ou ao preenchimento de preços dos cenários.',
    )
    st.caption('A fonte e o campo original são preservados. Descrição e papel semântico podem ser revisados sem recriar a coluna.')
    if st.button('Salvar alterações',type='primary',width='stretch'):
        provenance['description']=description.strip()
        mappings=dict(st.session_state.get('semantic_mappings',{}))
        if mappings.get('treasury')==field_name: mappings['treasury']=None
        if mappings.get('reference_price')==field_name: mappings['reference_price']=None
        if semantic_role=='Ações em tesouraria': mappings['treasury']=field_name
        elif semantic_role=='Preço de referência': mappings['reference_price']=field_name
        st.session_state.semantic_mappings=mappings
        project=st.session_state._project
        commit_foundation(project,foundation_payload())
        changed=adopt_global_treasury_mapping(project)
        if changed and active_draft(st.session_state._project):
            st.session_state.treasury_override_enabled=False
            st.session_state.treasury_override_explicit=False
        save_project(WORKSPACE_FILE,project)
        st.rerun()

def base_column_config(base_view):
    config={}
    for column in base_view.columns:
        if str(column).casefold()=='main_id':
            help_text='Identificador canônico do registro na tabela-base.'
        else:
            help_text=provenance_description(st.session_state.base_provenance.get(column,{}))
        config[column]=st.column_config.Column(str(column),help=help_text)
    return config

def _append_formula_token(state_key, token):
    st.session_state[state_key]=st.session_state.get(state_key,'')+token

def _formula_palette(variables, state_key, descriptions=None):
    st.caption('Use ponto como separador decimal: `0.25`, não `0,25`. A vírgula separa argumentos de funções.')
    st.markdown('##### Campos e variáveis disponíveis')
    if variables:
        def add(name): _append_formula_token(state_key,str(name))
        _compact_button_row(variables,key_prefix=f'{state_key}_var',callback=add,
                            help_text='Clique para inserir na função')
        with st.expander('Descrição dos campos'):
            for name in variables:
                desc=(descriptions or {}).get(name,'')
                st.markdown(f'`{name}`' + (f' · {desc}' if desc else ''))
    else:
        st.caption('Nenhum campo disponível. Adicione colunas à tabela-base primeiro.')
    with st.expander('Operações e funções'):
        for op,desc in {
            '+':'soma','-':'subtração','*':'multiplicação','/':'divisão','**':'potência',
            'sqrt(x)':'raiz quadrada','exp(x)':'exponencial','log(x)':'log natural',
            'abs(x)':'valor absoluto','min(a,b)':'menor valor','max(a,b)':'maior valor',
            'clamp(x,a,b)':'limita x ao intervalo [a,b]',
        }.items(): st.markdown(f'`{op}` · {desc}')

@st.dialog('Configurar variável',width='large')
def variable_dialog(edit_name=None):
    current=next((r for r in st.session_state.derived_defs
                  if str(r.get('Nome','')).casefold()==str(edit_name or '').casefold()),{})
    token=edit_name or 'new'
    name=st.text_input('Nome',value=str(current.get('Nome','')),key=f'var_name_{token}',placeholder='Ex.: LIQUIDEZ')
    description=st.text_input('Descrição',value=str(current.get('Descrição','')),key=f'var_desc_{token}',placeholder='O que este conceito representa?')
    expr_key=f'var_expr_{token}'
    if expr_key not in st.session_state: st.session_state[expr_key]=str(current.get('Função',''))
    available=primitive_names()+[n for n in derived_map() if n.casefold()!=str(edit_name or '').casefold()]
    _formula_palette(available,expr_key,{**primitive_descriptions(),**derived_descriptions()})
    expression=st.text_area('Função',key=expr_key,height=110,placeholder='Ex.: TURNOVER / max(FLOAT * PRICE, 1)')
    if expression.strip() and asset_ids():
        try:
            candidate={k:v for k,v in derived_map().items() if k.casefold()!=str(edit_name or '').casefold()}
            normalized=str(name).strip().upper() or '__PREVIEW__'
            candidate[normalized]=expression
            values=evaluate_derived(candidate,resolved_primitives(asset_ids()[0])[0])
            st.success(f'Prévia · {asset_ids()[0]} = {values[normalized]:,.6g}')
        except Exception as exc: st.info(f'Prévia indisponível: {_friendly_formula_error(exc)}')
    if st.button('Salvar variável',type='primary',width='stretch'):
        try:
            normalized=validate_unique_name(name,[r.get('Nome','') for r in st.session_state.derived_defs],ignore=edit_name)
            if not expression.strip(): raise ValueError('informe a função')
            candidate={k:v for k,v in derived_map().items() if k.casefold()!=str(edit_name or '').casefold()}
            candidate[normalized]=expression
            dependency_graph(candidate,set(primitive_names()))
            rows=[r for r in st.session_state.derived_defs if str(r.get('Nome','')).casefold()!=str(edit_name or '').casefold()]
            rows.append({'Nome':normalized,'Função':expression.strip(),'Descrição':description.strip()})
            st.session_state.derived_defs=rows
            persist_workspace()
            st.rerun()
        except Exception as exc: st.error(_friendly_formula_error(exc))

@st.dialog('Configurar função',width='large')
def formula_dialog(label, target_key, variables, descriptions=None):
    st.subheader(label)
    draft_key=f'formula_draft_{target_key}'
    if draft_key not in st.session_state: st.session_state[draft_key]=st.session_state.get(target_key,'')
    _formula_palette(variables,draft_key,descriptions)
    value=st.text_area('Função',key=draft_key,height=120,placeholder='Digite a expressão')
    if value.strip():
        try:
            preview=evaluate(value,{str(name):1.0 for name in variables})
            st.success(f'Validação sintática OK · cenário unitário = {preview:,.6g}')
        except Exception as exc: st.info(f'Função ainda inválida: {_friendly_formula_error(exc)}')
    if st.button('Salvar função',type='primary',width='stretch'):
        try:
            if not value.strip(): raise ValueError('informe a função')
            evaluate(value,{str(name):1.0 for name in variables})
            st.session_state[target_key]=value.strip()
            st.session_state.pop(draft_key,None)
            persist_workspace()
            st.rerun()
        except Exception as exc: st.error(_friendly_formula_error(exc))

def formula_summary(label,key,description,variables,descriptions=None):
    expr=str(st.session_state.get(key,'')).strip()
    left,right=st.columns([4,1])
    with left:
        st.markdown(f'**{label}**')
        st.caption(description)
        if expr: st.code(expr,language=None)
        else: st.warning('Ainda não configurada.')
    if right.button('Configurar' if not expr else 'Editar',key=f'open_{key}',width='stretch'):
        formula_dialog(label,key,variables,descriptions)

if page == 'Dados':
    tab_intro('Dados'); st.header('Base de ativos e fontes')
    st.caption('A **Base de ativos** serve somente para definir quais tickers (ou identificadores equivalentes) fazem parte do experimento. O campo canônico é sempre `main_id`. Depois de congelada, as demais fontes apenas enriquecem essa base por interseção; elas nunca criam ativos implicitamente.')
    base_full=st.session_state.base_table
    base_view=visible_base(base_full)
    has_base=not base_full.empty

    def _base_draft_init():
        st.session_state.base_draft=st.session_state.base_table.copy()
        st.session_state.base_undo=[]
        st.session_state.base_manual_input=''
        st.session_state.base_main_ref=''
        st.session_state.base_draft_ready=True

    def _base_push_undo():
        hist=st.session_state.setdefault('base_undo',[])
        hist.append(st.session_state.base_draft.copy())
        if len(hist)>30: del hist[:-30]

    def _base_add_manual_from_input():
        raw=str(st.session_state.get('base_manual_input','')).strip()
        if not raw: return
        _base_push_undo()
        st.session_state.base_draft=add_manual_base_ids(st.session_state.base_draft,[raw])
        st.session_state.base_manual_input=''

    def _base_remove_id(mid:str):
        _base_push_undo()
        d=st.session_state.base_draft
        st.session_state.base_draft=d.loc[d.main_id.astype(str)!=str(mid)].reset_index(drop=True)

    def _base_undo():
        hist=st.session_state.get('base_undo',[])
        if hist: st.session_state.base_draft=hist.pop()

    def _clear_base_ref():
        st.session_state.base_main_ref=''

    @st.dialog('Alterar Base de ativos',width='large')
    def base_dialog():
        if not st.session_state.get('base_draft_ready',False): _base_draft_init()
        draft=st.session_state.base_draft
        st.info('A Base de ativos define somente **quais identificadores existem no experimento**. `main_id` é o pilar canônico usado para cruzar todas as fontes posteriores. Use ticker ou um identificador equivalente e estável.')
        if st.session_state.get('base_import_notice'):
            st.success(st.session_state.pop('base_import_notice'))

        if not draft.empty:
            st.markdown('##### `main_id` atuais')
            st.caption('Clique em uma box para removê-la do rascunho. **Undo** restaura a última alteração. Nada é aplicado à tabela-base até **Salvar alterações**.')
            for origin,label in [('import','Importados'),('manual','Adicionados manualmente')]:
                group=draft.loc[draft['__base_origin__'].astype(str)==origin,'main_id'].astype(str).tolist()
                if origin=='import': group=sorted(group,key=str.casefold)
                if not group: continue
                st.caption(f'**{label}**')
                _compact_button_row(group,key_prefix=f'base_chip_{origin}',callback=_base_remove_id,callback_args=lambda mid:(mid,),help_text='Clique para remover do rascunho')
            a,b=st.columns([1,5])
            a.button('↶ Undo',disabled=not bool(st.session_state.get('base_undo')),on_click=_base_undo,use_container_width=True)
            b.caption(f'{len(draft)} identificadores no rascunho · alterações só são persistidas ao salvar.')
        else:
            st.caption('O rascunho está vazio. Importe identificadores abaixo ou adicione-os manualmente.')

        pending_import=None
        st.divider(); st.markdown('##### Importar identificadores')
        st.caption('A importação apenas alimenta `main_id`. Ela não adiciona ADV, market cap ou qualquer outra variável. A resposta é congelada como snapshot da base.')
        files=discover_local_sources(SOURCES_DIR); files=[f for f in files if f!='__api_preview__.json']
        if files:
            file=st.selectbox('Fonte',files,key='base_file',on_change=_clear_base_ref)
            info=inspect_snapshot(SOURCES_DIR/file); opts=[x['path'] for x in info['collections']]
            collection=st.selectbox('Coleção',opts,key='base_collection',on_change=_clear_base_ref,help='Em JSON nested, escolha a coleção. `root` significa que a raiz já é a relação.')
            header_row=0
            if info['format'] in {'CSV','XLSX'}:
                candidates=header_candidates(SOURCES_DIR/file,collection); suggested=suggested_header_row(SOURCES_DIR/file,collection)
                rows=sorted({x['row'] for x in candidates})
                header_row=st.selectbox('Linha de cabeçalho',rows,index=rows.index(suggested) if suggested in rows else 0,format_func=lambda x:f'Linha {x+1}',help='Use quando houver títulos/notas antes da tabela real.')
                with st.expander('Inspecionar linhas candidatas'):
                    st.dataframe(pd.DataFrame(candidates).sort_values('row')[['row','preview']].head(10),hide_index=True,width='stretch',column_config={'row':'linha','preview':'conteúdo detectado'})
            src=load_relation(SOURCES_DIR/file,collection,header_row=header_row)
            st.caption(f'{info["format"]} · {len(src)} registros · {len(src.columns)} campos')
            st.markdown('**5 primeiros resultados da fonte**')
            st.dataframe(src.head(5),hide_index=True,width='stretch')

            ref=_reference_editor('Definir identificador base (`main_id`)',list(src.columns),'base_main_ref','',base_identifier=True)
            st.caption('Os blocos acima são **campos da fonte**, não campos da Base de ativos. Escolha/compose o campo que representa o ticker ou identificador equivalente. Não há preenchimento automático.')
            if ref.strip():
                try:
                    pv=[eval_reference(ref,r) for r in src.head(5).to_dict('records')]
                    st.markdown('**5 primeiros `main_id` resultantes**')
                    st.dataframe(pd.DataFrame({'main_id':pv}),hide_index=True,width='stretch')
                except Exception as exc: st.info(_friendly_reference_error(exc, ref if 'ref' in locals() else ''))

            preserve=st.checkbox('Preservar `main_id` manuais ao substituir importados',value=True,help='A substituição troca somente a parcela importada. Registros manuais permanecem por padrão.')
            if ref.strip(): pending_import=(src,ref,file,collection,preserve)
        else:
            st.warning('Adicione CSV, XLSX ou JSON em `data/sources/`.')

        st.divider(); st.markdown('##### Adicionar manualmente')
        st.caption('Digite um identificador e pressione **Enter**. Ele vira uma box acima; clique na box para removê-lo.')
        st.text_input('Novo `main_id`',key='base_manual_input',placeholder='Ex.: PETR4',on_change=_base_add_manual_from_input)

        st.markdown('''<style>
        .st-key-base_save_bar{position:sticky;bottom:0;z-index:999;background:var(--background-color);padding:.65rem 0 .2rem 0;border-top:1px solid rgba(128,128,128,.28)}
        </style>''',unsafe_allow_html=True)
        with st.container(key='base_save_bar'):
            csave,creset=st.columns([3,1])
            if csave.button('Salvar Base de ativos',type='primary',width='stretch'):
                try:
                    candidate=st.session_state.base_draft.copy()
                    if pending_import is not None:
                        import_src,import_ref,import_file,import_collection,keep_manual=pending_import
                        manual=candidate.loc[candidate.get('__base_origin__',pd.Series(index=candidate.index,dtype=str)).eq('manual')] if keep_manual and not candidate.empty else None
                        candidate=build_base_snapshot(import_src,import_ref,origin=f'{import_file} · {import_collection}',existing_manual=manual)
                    meta_cols=['main_id','__base_origin__','__base_detail__']
                    candidate=candidate[[c for c in meta_cols if c in candidate.columns]].copy()
                    previous=st.session_state.base_table
                    observed=[c for c in visible_base(previous).columns if c!='main_id']
                    if observed:
                        candidate=candidate.merge(previous[['main_id']+observed],on='main_id',how='left')
                    st.session_state.base_table=candidate
                    st.session_state.base_provenance={k:v for k,v in st.session_state.base_provenance.items() if k in candidate.columns}
                    st.session_state.source_cache={}; st.session_state.base_draft=candidate.copy(); st.session_state.base_draft_ready=False
                    persist_workspace(); st.rerun(scope='app')
                except Exception as exc: st.error(str(exc))
            if creset.button('Descartar',width='stretch'):
                st.session_state.base_draft_ready=False
                st.rerun()

    if not has_base:
        c1,c2=st.columns([1,3])
        if c1.button('＋ Criar Base de ativos',type='primary',width='stretch'): base_dialog()
        c2.caption('Comece definindo apenas os `main_id`. Você pode digitá-los manualmente ou importar registros de CSV, XLSX ou JSON; a importação é congelada como snapshot.')
        st.dataframe(pd.DataFrame(columns=['main_id']),hide_index=True,width='stretch')
    else:
        # Render from the canonical state immediately before displaying it.
        base_full=st.session_state.base_table
        base_view=visible_base(base_full)
        st.caption(f'{len(base_full)} ativos congelados · {int((base_full.__base_origin__=="import").sum())} importados · {int((base_full.__base_origin__=="manual").sum())} manuais')
        st.subheader('Tabela-base')
        st.dataframe(base_view.reset_index(drop=True),hide_index=True,width='stretch',height=340,column_order=list(base_view.columns),column_config=base_column_config(base_view))
        a,b=st.columns([1,4])
        if a.button('＋ Adicionar fonte',type='primary',width='stretch'): relational_source_dialog()
        b.caption('Fontes adicionais fazem **interseção** com `main_id`. CSV/XLSX/JSON usam referências base ↔ fonte; APIs podem consumir campos já agregados.')
        st.markdown('##### Gerenciar colunas')
        deletable=[c for c in base_view.columns if c!='main_id']
        todel=st.multiselect('Colunas para deletar',deletable,placeholder='Selecione uma ou mais colunas')
        if st.button('Deletar colunas selecionadas',disabled=not bool(todel)):
            st.session_state.base_table=st.session_state.base_table.drop(columns=todel)
            for c in todel: st.session_state.base_provenance.pop(c,None)
            st.session_state.source_cache={}; persist_workspace(); st.rerun()
        st.caption('`main_id` só pode ser alterado em **Alterar base**. Nomes de coluna são únicos sem distinguir maiúsculas/minúsculas.')
        with st.expander('Origem dos main_id'):
            origins=base_full[['main_id','__base_origin__','__base_detail__']].rename(columns={'__base_origin__':'Origem','__base_detail__':'Detalhe'})
            st.dataframe(origins,hide_index=True,width='stretch')
        with st.expander('Proveniência das colunas'):
            rows=[]
            for c in base_view.columns:
                p=st.session_state.base_provenance.get(c,{'source':'Base de ativos','kind':'identity'})
                rows.append({'Coluna':c,'Fonte':p.get('source','Base de ativos'),'Descrição':p.get('description',''),'Campo original':p.get('field',''),'Coleção':p.get('collection',''),'Tipo':p.get('kind','identity')})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
            editable_descriptions=[c for c in base_view.columns if c!='main_id']
            if editable_descriptions:
                edit_col,edit_action=st.columns([3,1])
                edit_field=edit_col.selectbox('Coluna para revisar',editable_descriptions,key='data_description_target')
                if edit_action.button('Revisar coluna',key='edit_data_description',width='stretch'):
                    primitive_description_dialog(edit_field)
        st.divider()
        maintenance,description=st.columns([1,4])
        if maintenance.button('Alterar base',width='stretch'): base_dialog()
        description.caption('Altere o universo de `main_id` da tabela-base. Esta é uma operação estrutural.')

if page == 'Variáveis':
    tab_intro('Variáveis'); st.header('Conceitos intermediários')
    st.caption('Colunas da tabela-base são dados observados. Variáveis são conceitos calculados a partir delas ou de outras variáveis.')
    if not asset_ids():
        st.warning('Crie a Base de ativos na aba **Dados** antes de definir variáveis.')
    elif not primitive_names():
        st.info('A base já define o universo, mas ainda não possui dados observados. Adicione uma fonte na aba **Dados**.')
    else:
        st.markdown('##### Dados observados disponíveis')
        st.dataframe(pd.DataFrame(primitive_metadata_rows()),hide_index=True,width='stretch')
        observed_col,observed_action=st.columns([3,1])
        observed_field=observed_col.selectbox('Dado observado para revisar',primitive_names(),key='observed_description_target')
        if observed_action.button('Revisar coluna',width='stretch'): primitive_description_dialog(observed_field)
        action,description=st.columns([1,4])
        if action.button('＋ Adicionar variável',type='primary',width='stretch'): variable_dialog()
        description.caption('Crie conceitos reutilizáveis sem alterar os dados observados da tabela-base.')
    if st.session_state.derived_defs:
        st.subheader('Variáveis definidas')
        for row in st.session_state.derived_defs:
            name=str(row.get('Nome',''))
            a,b,c=st.columns([5,1,1])
            with a:
                st.markdown(f'**{name}** · {row.get("Descrição","") or "sem descrição"}')
                st.code(str(row.get('Função','')),language=None)
            if b.button('Editar função/descrição',key=f'edit_var_{name}',width='stretch'): variable_dialog(name)
            if c.button('Excluir',key=f'del_var_{name}',width='stretch'):
                dependents=direct_dependents(derived_map(),name)
                if dependents: st.error(f'{name} ainda é usada por: {", ".join(dependents)}')
                else:
                    st.session_state.derived_defs=[r for r in st.session_state.derived_defs if str(r.get('Nome',''))!=name]; persist_workspace(); st.rerun()
        st.subheader('Valores resultantes')
        try:
            vals=[]
            for main_id in asset_ids():
                vv=all_vars_for(main_id); vals.append({'main_id':main_id,**{k:vv[k] for k in derived_map()}})
            st.dataframe(pd.DataFrame(vals),hide_index=True,width='stretch',height=300)
        except Exception as exc: st.error(f'Não foi possível resolver as variáveis: {_friendly_formula_error(exc)}')
    st.divider(); st.subheader('Dependências e explicação')
    concepts=list(derived_map())
    if concepts:
        c1,c2=st.columns([.45,.55],gap='large')
        with c1:
            target=st.selectbox('Conceito',concepts,key='dep_target')
            ticker=st.selectbox('Registro de referência',asset_ids(),key='dep_ticker')
            row=next((x for x in st.session_state.derived_defs if str(x.get('Nome','')).strip().upper()==target),{})
            st.markdown(f'**{target}** · {row.get("Descrição","") or "sem descrição"}')
            st.code(derived_map()[target],language=None)
            try:
                layers=dependency_layers(target,derived_map(),set(resolved_primitives(ticker)[0]))
                for depth,names in enumerate(layers):
                    label='Resultado' if depth==0 else ('Depende diretamente de' if depth==1 else f'Nível {depth}')
                    st.markdown(f'**{label}:** '+ '  →  '.join(f'`{n}`' for n in names))
            except Exception as exc: st.error(_friendly_formula_error(exc))
        with c2:
            try:
                prim,obs=resolved_primitives(ticker)
                descriptions={**primitive_descriptions(),**derived_descriptions()}
                trace=explain_dependency(target,derived_map(),prim,descriptions)
                obs_map={o.variable:o for o in obs}
                rows=[]
                for x in trace:
                    o=obs_map.get(x['name'])
                    rows.append({'Caminho':'    '*int(x['depth']) + ('↳ ' if x['depth'] else '') + str(x['name']),'Tipo':x['kind'],'Valor':x['value'],'Definição':x['expression'] or 'observado','Descrição':x['description'],'Fonte':o.source if o else 'calculado'})
                st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch',height=390)
                st.caption('A explicação percorre o resultado até os dados primitivos. Conceitos intermediários são calculados; folhas primitivas preservam sua fonte.')
            except Exception as exc: st.error(f'Não foi possível explicar {target}: {_friendly_formula_error(exc)}')
    else: st.info('Crie ao menos um conceito intermediário para visualizar suas dependências.')
    st.divider(); st.subheader('Mapeamentos semânticos')
    st.caption('Estes vínculos pertencem à base analítica e são compartilhados por todas as especificações. Alterá-los muda a interpretação dos dados, não a regra experimental.')
    semantic_fields=primitive_names()+[name for name in derived_map() if name not in primitive_names()]
    if 'semantic_treasury_widget' not in st.session_state: st.session_state.semantic_treasury_widget=semantic_mapping('treasury')
    if 'semantic_reference_price_widget' not in st.session_state: st.session_state.semantic_reference_price_widget=semantic_mapping('reference_price')
    treasury_options=semantic_field_options(semantic_fields,semantic_mapping('treasury'))
    price_options=semantic_field_options(semantic_fields,semantic_mapping('reference_price'))
    mapping_left,mapping_right=st.columns(2)
    mapping_left.selectbox('Campo que representa ações em tesouraria',treasury_options,key='semantic_treasury_widget',format_func=lambda value:'— selecione —' if value is None else value,on_change=persist_semantic_mappings,args=('treasury',),help='Dado observado ou variável que representa o saldo de ações mantidas em tesouraria pela companhia.')
    mapping_right.selectbox('Campo que representa o preço de referência',price_options,key='semantic_reference_price_widget',format_func=lambda value:'— selecione —' if value is None else value,on_change=persist_semantic_mappings,args=('reference_price',),help='Dado observado ou variável usado como preço atual para preencher e revisar as ordens dos cenários.')
    if semantic_mapping('treasury'):
        st.caption(f"Todas as especificações usam `{semantic_mapping('treasury')}` como Treasury, salvo quando um override experimental estiver explicitamente ativo.")
    if semantic_mapping('reference_price'):
        st.caption(f"Todos os cenários usam `{semantic_mapping('reference_price')}` como preço de referência da companhia selecionada.")

if page == 'Especificações' and experiment_section == 'Memória':
    tab_intro('Memória'); st.header('Estado informacional')
    memory_desc={'I':'estado anterior','U':'utilização da capacidade','STREAK':'persistência direcional','REV':'1 quando há reversão','I_MULT':'multiplicador do estado informacional','I_DECAYED':'estado após decay','SIGNAL':'resultado da função de sinal','DT':'tempo transcorrido','GAIN':'ganho','ACCEL':'aceleração','REV_PENALTY':'penalidade de reversão','LAMBDA':'taxa de decay'}
    formula_summary('1 · Sinal da janela','signal_expr','Transforma a utilização e o estado da janela em sinal.',['I','U','STREAK','REV','I_MULT'],memory_desc)
    formula_summary('2 · Atualização do estado','update_expr','Combina memória decaída e novo sinal.',['I','I_DECAYED','U','SIGNAL','STREAK','REV','GAIN','ACCEL','REV_PENALTY'],memory_desc)
    formula_summary('3 · Decay','decay_expr','Determina como a memória envelhece entre janelas.',['I','DT','LAMBDA'],memory_desc)
    st.divider(); st.subheader('Parâmetros')
    st.caption('O ícone de ajuda ao lado de cada campo explica sua função e unidade de referência.')
    a,b,c,d=st.columns(4)
    a.number_input('Ganho da atualização (GAIN)',min_value=0.,step=.05,key='GAIN',help='Quanto uma janela utilizada acrescenta ao estado informacional. Na fórmula padrão, U=100% acrescenta GAIN antes dos demais ajustes.')
    b.number_input('Taxa de decay (LAMBDA)',min_value=0.,step=.05,key='LAMBDA',help='Velocidade de perda da memória. Na fórmula exponencial padrão, DT é medido em intervalos entre janelas; valores maiores apagam o estado mais rápido.')
    c.number_input('Aceleração da persistência (ACCEL)',min_value=0.,step=.05,key='ACCEL',help='Acréscimo aplicado quando há janelas consecutivas na mesma direção. Zero desativa a aceleração por persistência.')
    d.number_input('Escala do estado (I_MULT)',min_value=0.,step=.05,key='I_MULT',help='Converte o estado I no sinal usado pela capacidade. Na fórmula padrão, 1 preserva a escala; acima de 1 faz a saturação chegar mais cedo.')
    st.number_input('Penalidade de reversão (REV_PENALTY)',min_value=0.,max_value=1.,step=.05,key='REV_PENALTY',help='Redução do incremento de memória quando a direção se inverte. 0 não penaliza; 1 elimina integralmente o novo incremento na fórmula padrão.')
    if st.session_state.LAMBDA>0 and 'exp(' in st.session_state.decay_expr:
        st.caption(f'Na curva exponencial atual, metade do estado permanece após aproximadamente **{math.log(2)/st.session_state.LAMBDA:.2f} intervalos de DT**.')
    try:
        rr=current_hrule(); curves=[{'Δt':dt,'I restante':rr.decay(1.,dt,{'LAMBDA':st.session_state.LAMBDA})} for dt in [x/10 for x in range(101)]]
        st.altair_chart(alt.Chart(pd.DataFrame(curves)).mark_line().encode(x=alt.X('Δt:Q',scale=alt.Scale(domain=[0,10])),y=alt.Y('I restante:Q',scale=alt.Scale(domain=[0,1])),tooltip=['Δt','I restante']).properties(height=300),width='stretch')
    except Exception as exc: st.error(_friendly_formula_error(exc))

if page == 'Especificações' and experiment_section == 'Capacidade':
    tab_intro('Capacidade'); st.header('Funções de capacidade'); available=primitive_names()+list(derived_map())
    descriptions={**primitive_descriptions(),**derived_descriptions()}
    if not asset_ids(): st.warning('Crie a Base de ativos na aba **Dados** antes de configurar H.')
    elif not available: st.info('Adicione dados observados ou variáveis antes de configurar H.')
    st.subheader('H₀')
    formula_summary('H₀ gross','h0_gross_expr','Capacidade bruta inicial.',available,descriptions)
    formula_summary('H₀ net+','h0_plus_expr','Capacidade direcional de compra inicial.',available,descriptions)
    formula_summary('H₀ net−','h0_minus_expr','Capacidade direcional de venda inicial.',available,descriptions)
    st.subheader('Hmax e saturação'); formula_summary('Hmax','hmax_expr','Limite superior da progressão de capacidade.',['H0']+available,{'H0':'capacidade-base calculada',**descriptions})
    sat_options=['hyperbolic','exponential','linear','power']
    c1,c2=st.columns(2)
    c1.selectbox('Família da resposta',sat_options,key='sat_kind',help='Define como o sinal normalizado é convertido em capacidade. O gráfico abaixo é a referência visual comum entre as famílias.')
    c2.number_input('Curvatura matemática (k)',min_value=.01,step=.1,key='sat_shape',disabled=st.session_state.sat_kind=='linear',help='Controla quão cedo a resposta se aproxima de Hmax. Não há uma escala universal entre famílias; compare a curva e os pontos de referência abaixo. A família linear ignora k.')
    st.caption('Em todas as famílias: sinal 0% → H₀ e sinal 100% → Hmax. Use a curva como referência; k não é diretamente comparável entre famílias.')
    response=pd.DataFrame([{'Sinal':x/100,'Resposta':endpoint_saturation(x/100,st.session_state.sat_kind,st.session_state.sat_shape)} for x in range(101)])
    response_chart=alt.Chart(response).mark_line().encode(x=alt.X('Sinal:Q',axis=alt.Axis(format='%')),y=alt.Y('Resposta:Q',axis=alt.Axis(format='%'),scale=alt.Scale(domain=[0,1])),tooltip=[alt.Tooltip('Sinal:Q',format='.0%'),alt.Tooltip('Resposta:Q',format='.1%')]).properties(height=230)
    st.altair_chart(response_chart,width='stretch')
    refs=[{'Sinal':f'{x:.0%}','Resposta da capacidade':f'{endpoint_saturation(x,st.session_state.sat_kind,st.session_state.sat_shape):.1%}'} for x in (.25,.5,.75)]
    st.dataframe(pd.DataFrame(refs),hide_index=True,width='stretch')
    try:
        tbl=[]
        for t in asset_ids():
            g,p,n=h0_for_new(t); tbl.append({'main_id':t,'H₀ gross':g,'H₀ net+':p,'H₀ net−':n})
        st.dataframe(pd.DataFrame(tbl),hide_index=True,width='stretch')
    except Exception as exc: st.error(_friendly_formula_error(exc))

    st.divider(); st.header('Trajetória entre janelas'); st.caption('A atualização ocorre no fechamento de cada janela: U total atualiza a memória e determina a capacidade da janela seguinte.')
    l,r=st.columns([.7,1.4],gap='large')
    with l:
        ids=asset_ids()
        if not ids: st.warning('Crie a Base de ativos na aba **Dados**.'); ticker=None
        else: ticker=st.selectbox('Registro',ids,key='seq_ticker2')
        steps=st.number_input('Janelas',1,100,12); u=st.number_input('U por janela',0.,1.,.70,.05); reversal=st.number_input('Reversão no passo',0,int(steps),0)
    with r:
        try:
            if ticker is None: raise ValueError('nenhum registro disponível')
            _,h0,_=h0_for_new(ticker); d=progression(ticker,h0,int(steps),u,int(reversal)); line_chart(d,['H','Hmax']); st.dataframe(d,hide_index=True,width='stretch',height=390)
        except Exception as exc: st.error(_friendly_formula_error(exc))

def persist_intrawindow_controls(config_name,mark_override=False):
    """Persist coupled Intrawindow controls atomically before Streamlit reruns."""
    project=st.session_state._project
    draft=active_draft(project)
    if not draft: return
    iw=draft.setdefault('config',{}).setdefault('intrawindow',{})
    qg_key=f'iw_qg_{config_name}'; qp_key=f'iw_qp_{config_name}'; qm_key=f'iw_qm_{config_name}'
    iw.update({
        'rho_gross':float(st.session_state.get(qg_key,float(iw.get('rho_gross',.5))*100))/100.0,
        'rho_plus':float(st.session_state.get(qp_key,float(iw.get('rho_plus',.5))*100))/100.0,
        'rho_minus':float(st.session_state.get(qm_key,float(iw.get('rho_minus',.5))*100))/100.0,
        'treasury_override_enabled':bool(st.session_state.get('treasury_override_enabled',iw.get('treasury_override_enabled',False))),
        'treasury_override':float(st.session_state.get('treasury_override',iw.get('treasury_override',0.0)) or 0.0),
        'position_limit_enabled':bool(st.session_state.get('position_limit_enabled',iw.get('position_limit_enabled',False))),
        'position_limit_field':st.session_state.get('position_limit_field',iw.get('position_limit_field')),
        'position_limit_ratio':float(st.session_state.get('position_limit_ratio',iw.get('position_limit_ratio',25.0)) or 25.0),
        'topology':'calendar',
    })
    if mark_override:
        iw['treasury_override_explicit']=True
        st.session_state.treasury_override_explicit=True
    current=st.session_state.configs.get(config_name)
    if current:
        st.session_state.configs[config_name]=replace(current,rho_gross=iw['rho_gross'],rho_plus=iw['rho_plus'],rho_minus=iw['rho_minus'])
    save_project(WORKSPACE_FILE,project)

if page == 'Especificações' and experiment_section == 'Intrawindow':
    tab_intro('Intrawindow')
    st.info('**Ciclo da regra:** durante o pregão, cruzar Q gera um alerta ao emissor, mas ainda não decide o disclosure. No fechamento, Q é avaliado sobre os valores finais; depois U atualiza a memória e a capacidade da próxima janela. A execução residual continua permitida até H.')
    left,right=st.columns([.82,1.45],gap='large')
    with left:
        st.header('Regra da janela'); names=list(st.session_state.configs); active=st.selectbox('Cenário de Q e trajetória',names,key='iw_config'); c=st.session_state.configs[active]
        st.subheader('1 · Capacidade travada na abertura')
        ids=asset_ids(); ticker=None; calculated=None
        if not ids:
            st.warning('Crie a Base de ativos e configure as funções de H antes de simular uma janela.')
        else:
            if st.session_state.get('iw_ticker') not in ids: st.session_state.pop('iw_ticker',None)
            ticker=st.selectbox('Registro da Base',ids,key='iw_ticker',help='Dados observados e variáveis calculadas deste registro alimentam H₀, Hmax e a função de capacidade.')
        information=st.number_input('Estado informacional na abertura (I)',min_value=0.,max_value=1.,step=.05,key='iw_opening_information',help='Estado consolidado herdado da janela anterior. I=0 usa a capacidade estrutural H₀; valores maiores percorrem a função de resposta configurada.')
        if ticker is not None:
            try:
                h0_values,calculated=opening_capacity(ticker,information)
                capacity_preview=pd.DataFrame([
                    {'Dimensão':'Gross','H₀':h0_values[0],'H travado na abertura':calculated[0]},
                    {'Dimensão':'Net+','H₀':h0_values[1],'H travado na abertura':calculated[1]},
                    {'Dimensão':'Net−','H₀':h0_values[2],'H travado na abertura':calculated[2]},
                ])
                st.dataframe(capacity_preview,hide_index=True,width='stretch')
                st.caption(f'Capacidade calculada para **{ticker}** pela cadeia Dados → Variáveis → H₀/Hmax → estado I.')
            except Exception as exc:
                st.error('Não foi possível calcular H para este registro: '+_friendly_formula_error(exc))
        manual_override=st.checkbox('Usar override experimental de H',value=False,help='Ignora temporariamente a capacidade calculada. Serve para testes isolados e não altera as funções configuradas na aba Capacidade.')
        if manual_override:
            defaults=calculated or (c.h_gross,c.h_plus,c.h_minus)
            hg=st.number_input('H gross · override',0.,value=float(defaults[0]),step=10_000.,help='Limite rígido experimental de execução bruta.'); hp=st.number_input('H net+ · override',0.,value=float(defaults[1]),step=10_000.,help='Limite direcional experimental para compras.'); hm=st.number_input('H net− · override',0.,value=float(defaults[2]),step=10_000.,help='Limite direcional experimental para vendas.')
            if hg<max(hp,hm): st.warning('H gross deve ser pelo menos igual ao maior limite direcional.'); hg=max(hg,hp,hm)
        elif calculated is not None:
            hg,hp,hm=calculated
        else:
            hg=hp=hm=None
        st.subheader('2 · Limiar de disclosure (Q)')
        st.caption('Digite o percentual de H entre 0 e 100. Exemplo: `37,5` representa 37,5% e é convertido internamente para 0,375.')
        rg_pct=st.number_input('Q gross (% de H)',0.01,100.0,float(c.rho_gross)*100,0.5,format='%.2f',key=f'iw_qg_{active}',on_change=persist_intrawindow_controls,args=(active,),help='Ao atingir Q gross, o emissor recebe um alerta. Como Gross é acumulado, ele não diminui com operação oposta; a obrigação é confirmada no fechamento.'); rp_pct=st.number_input('Q net+ (% de H)',0.01,100.0,float(c.rho_plus)*100,0.5,format='%.2f',key=f'iw_qp_{active}',on_change=persist_intrawindow_controls,args=(active,),help='Alerta intraday para exposição líquida de compra. Se Net+ voltar abaixo de Q antes do fechamento, não há disclosure por esta dimensão.'); rm_pct=st.number_input('Q net− (% de H)',0.01,100.0,float(c.rho_minus)*100,0.5,format='%.2f',key=f'iw_qm_{active}',on_change=persist_intrawindow_controls,args=(active,),help='Alerta intraday para exposição líquida de venda. Se Net− voltar abaixo de Q antes do fechamento, não há disclosure por esta dimensão.')
        rg,rp,rm=rg_pct/100.0,rp_pct/100.0,rm_pct/100.0
        st.subheader('3 · Posição em tesouraria')
        numeric_fields=[]
        if ticker is not None:
            values=all_vars_for(ticker)
            numeric_fields=[name for name,value in values.items() if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value))]
        saved_position_field=st.session_state.get('position_limit_field')
        field_options=semantic_field_options(numeric_fields,saved_position_field)
        treasury_field=semantic_mapping('treasury')
        st.caption(f"Campo global: `{treasury_field}` · configurado em **Variáveis → Mapeamentos semânticos**." if treasury_field else 'Campo global ainda não configurado. Defina-o em **Variáveis → Mapeamentos semânticos**.')
        if ticker is not None and treasury_field and treasury_field not in numeric_fields:
            st.warning(f"O campo global `{treasury_field}` não pôde ser resolvido para {ticker}. Revise a Base e as Variáveis.")
        st.checkbox('Ignorar Treasury global e usar override experimental',key='treasury_override_enabled',on_change=persist_intrawindow_controls,args=(active,True),help='Substitui o campo definido em Variáveis apenas nesta especificação. Útil para testes de fronteira.')
        if st.session_state.treasury_override_enabled:
            st.number_input('Treasury inicial · override',min_value=0.,step=10_000.,key='treasury_override',on_change=persist_intrawindow_controls,args=(active,))
            tr=float(st.session_state.treasury_override)
            st.warning(f'Override experimental ativo: esta especificação ignora `{treasury_field or "campo global não configurado"}` e usa {tr:,.0f} ações em tesouraria.')
        elif ticker is not None and treasury_field and treasury_field in numeric_fields:
            tr=float(all_vars_for(ticker)[treasury_field])
            st.metric('Treasury inicial resolvida',f'{tr:,.0f}')
        else:
            tr=None
            st.warning('Selecione o campo de Treasury ou habilite o override manual para executar o cenário.')

        st.markdown('##### Limite opcional de posição própria')
        st.checkbox('Limitar Treasury após compras líquidas',key='position_limit_enabled',on_change=persist_intrawindow_controls,args=(active,),help='Hipótese experimental. Quando ativa, Treasury + Net+ não pode ultrapassar o percentual configurado do campo de referência.')
        if st.session_state.position_limit_enabled:
            st.selectbox('Campo de referência do limite',field_options,key='position_limit_field',format_func=lambda value:'— selecione —' if value is None else value,on_change=persist_intrawindow_controls,args=(active,),help='Selecione qualquer dado observado ou variável numérica que represente o denominador definido para esta especificação; o Lab não presume que seja free float ou total emitido.')
            if ticker is not None and st.session_state.get('position_limit_field') and st.session_state.position_limit_field not in numeric_fields:
                st.warning(f"O campo salvo `{st.session_state.position_limit_field}` não pôde ser resolvido para {ticker}. O vínculo foi preservado; revise a Base e as Variáveis.")
            st.number_input('Limite máximo (% do campo de referência)',min_value=.01,max_value=100.,step=.5,key='position_limit_ratio',format='%.2f',on_change=persist_intrawindow_controls,args=(active,))
        if hg is not None and tr is not None:
            hm=min(float(hm),tr)
            if st.session_state.position_limit_enabled:
                if not st.session_state.position_limit_field:
                    hp=None; st.warning('Selecione o campo de referência para aplicar o limite de posição.')
                else:
                    denominator=float(all_vars_for(ticker)[st.session_state.position_limit_field])
                    ceiling=denominator*float(st.session_state.position_limit_ratio)/100.0
                    headroom=max(0.,ceiling-tr)
                    hp=min(float(hp),headroom)
                    st.caption(f'Limite de posição: {ceiling:,.0f} · espaço líquido para compra: {headroom:,.0f}.')
            if hp is not None: hg=max(float(hg),float(hp),float(hm))
        current=Config(active,hg,hp,hm,rg,rp,rm,tr) if hg is not None and hp is not None and tr is not None else None
        if current is not None: st.session_state.configs[active]=current
        st.caption('A sequência de compras e vendas pertence à biblioteca global de **Cenários**.')
    with right:
        st.header('Comportamento')
        if current is None:
            st.info('Configure H para o registro selecionado ou habilite o override experimental para iniciar a simulação.')
        else:
            engine,df,error,capacity_notices=run(current,st.session_state.actions); w=engine.state.active_window; q=engine.state.thresholds
            a,b,c1,d=st.columns(4); a.metric('Gross',f'{w.gross:,.0f}'); b.metric('Net',f'{w.net:,.0f}'); c1.metric('Treasury',f'{engine.state.treasury:,.0f}'); d.metric('Eventos',len(engine.events))
            if error: st.error(error)
            if capacity_notices: st.warning(capacity_status(capacity_notices)+'. As quantidades solicitadas foram preservadas e o motor executou apenas o residual permitido.')
            cap=pd.DataFrame([{'Dimensão':'Gross','Utilizado':w.gross,'Q de disclosure':q.gross,'H · limite rígido':current.h_gross},{'Dimensão':'Net+','Utilizado':w.net_plus,'Q de disclosure':q.net_plus,'H · limite rígido':current.h_plus},{'Dimensão':'Net−','Utilizado':w.net_minus,'Q de disclosure':q.net_minus,'H · limite rígido':current.h_minus}]); st.dataframe(cap,hide_index=True,width='stretch')
            crossed=[]
            if w.gross>=q.gross: crossed.append('Gross')
            if w.net_plus>=q.net_plus: crossed.append('Net+')
            if w.net_minus>=q.net_minus: crossed.append('Net−')
            alerted=[dimension.value for dimension in sorted(w.q_crossed,key=lambda x:x.value)]
            if alerted: st.caption('Alertas intraday registrados: **'+', '.join(alerted)+'**. Eles permanecem no log mesmo que a exposição líquida volte abaixo de Q.')
            if crossed: st.warning('**Se o pregão fechasse agora**, haveria disclosure por: **'+', '.join(crossed)+'**. O residual continua executável até os respectivos H.')
            elif alerted: st.success('A exposição final simulada voltou abaixo dos Q aplicáveis. Se o pregão fechasse agora, não haveria disclosure — salvo outra dimensão ainda acima do limiar.')
            else: st.success('Nenhum alerta de Q ocorreu. A janela continua aberta e sujeita aos limites H.')
            st.caption('Linhas tracejadas representam Q; a linha vermelha em 100% representa H. O disclosure é decidido no fechamento.')
            intrawindow_chart(df,current); st.dataframe(df,hide_index=True,width='stretch',height=330)

def scenario_label(scenario):
    return f"{scenario.get('company','—')} · {scenario.get('strategy','Estratégia sem nome')}"

def bump_order_editor(scenario_id):
    key=f'order_editor_revision_{scenario_id}'
    st.session_state[key]=int(st.session_state.get(key,0))+1

def sync_scenario_order_editor(scenario_id, editor_key):
    """Commit the editor delta before Streamlit performs the widget rerun."""
    project=st.session_state._project
    owner=project.setdefault('scenarios',{'items':{},'active_id':None})
    scenario=owner.setdefault('items',{}).get(scenario_id)
    if not scenario:
        return
    updated=apply_editor_delta(st.session_state.get('actions',[]),st.session_state.get(editor_key,{}))
    st.session_state.actions=updated
    if owner.get('active_id')==scenario_id:
        commit_active_scenario(
            project,
            str(st.session_state.get('scenario_company_widget') or ''),
            str(st.session_state.get('scenario_strategy_widget') or ''),
            str(st.session_state.get('scenario_description_widget') or ''),
            updated,
        )
    else:
        scenario['actions']=updated
    save_project(WORKSPACE_FILE,project)
    # A fresh key clears the consumed delta, especially for added/deleted rows.
    bump_order_editor(scenario_id)

@st.dialog('Arquivar cenário')
def archive_scenario_dialog(scenario_id):
    project=st.session_state._project
    scenario=project.get('scenarios',{}).get('items',{}).get(scenario_id)
    if not scenario:
        st.warning('Este cenário já não está disponível.'); return
    st.warning(f"Você está arquivando **{scenario_label(scenario)}**. Ele sairá dos comparadores, mas poderá ser restaurado.")
    if st.button('Confirmar arquivamento',type='primary',width='stretch'):
        delete_scenario(project,scenario_id)
        reload_project(project,'Cenário arquivado. Ele pode ser restaurado na biblioteca.')

def evaluate_pair(experiment,scenario):
    ticker=scenario.get('company')
    if not ticker: raise ValueError('o cenário não possui companhia')
    actions=executable_actions(scenario.get('actions',[]))
    if not actions: raise ValueError('o cenário não possui ordens completas')
    config,capacity_resolution=resolved_saved_experiment(experiment,ticker,with_trace=True)
    result=execute_experiment(config,actions)
    result['capacity_resolution']=capacity_resolution
    return config,result

def capacity_resolution_caption(result):
    trace=result.get('capacity_resolution',{}).get('Net−',{})
    if not trace: return None
    calculated=float(trace.get('calculated',0.) or 0.)
    constraint=trace.get('constraint')
    effective=float(trace.get('effective',0.) or 0.)
    source=str(trace.get('source','H calculado'))
    if constraint is None:
        return f"**H net− efetivo:** {effective:,.0f} ações · limitante: H calculado."
    limiting='H calculado' if calculated<=float(constraint) else source
    return f"**H net−:** {calculated:,.0f} calculado · {float(constraint):,.0f} em {source} · **{effective:,.0f} efetivo** (limitante: {limiting})."

def render_evaluation_preview(experiment,scenario,key_prefix):
    """Render the same one-to-one evaluation in both contextual previews."""
    valid_actions=executable_actions(scenario.get('actions',[]))
    if not valid_actions:
        st.info('Adicione ao menos uma ordem com **quantidade e preço maiores que zero** para visualizar a prévia.')
        return None,None
    scenario={**scenario,'actions':valid_actions}
    try:
        config,result=evaluate_pair(experiment,scenario); w=result['final_window']
        m1,m2,m3,m4=st.columns(4)
        m1.metric('Gross final',f'{w.gross:,.0f}'); m2.metric('Net final',f'{w.net:,.0f}')
        m3.metric('Utilização gross',f'{w.utilization(CapacityDimension.GROSS):.1%}'); m4.metric('Divulgação','Sim' if result['disclosure'] else 'Não')
        st.caption(f"**{experiment['name']}** × **{scenario_label(scenario)}** · cálculo automático")
        st.caption('**Execução:** '+execution_status(result))
        resolution_caption=capacity_resolution_caption(result)
        if resolution_caption: st.caption(resolution_caption)
        summary_tab,audit_tab,event_tab,check_tab=st.tabs(['Resumo e trajetória','Auditoria causal','Eventos','Invariantes'])
        with summary_tab:
            if result['error']: st.error('Trajetória interrompida: '+result['error'])
            if result['capacity_notices']:
                execution_phrase='A ordem foi executada' if len(result['capacity_notices'])==1 else 'As ordens foram executadas'
                st.warning(capacity_status(result['capacity_notices'])+f'. {execution_phrase} parcialmente até o limite; o residual não foi executado.')
            if result['disclosure']: st.warning('**'+disclosure_status(result['disclosure'])+'**.')
            else: st.success('Sem divulgação no fechamento: nenhuma dimensão terminou acima de Q.')
            intrawindow_chart(result['trajectory'],config)
        with audit_tab: st.dataframe(result['audit'],hide_index=True,width='stretch',height=360,key=f'{key_prefix}_audit')
        with event_tab: st.dataframe(result['events'],hide_index=True,width='stretch',height=360,key=f'{key_prefix}_events')
        with check_tab: st.dataframe(result['checks'],hide_index=True,width='stretch',key=f'{key_prefix}_checks')
        evaluation_id=rules_fingerprint({'experiment':experiment['id'],'experiment_config':experiment['config'],'scenario':scenario})
        st.session_state.experiment_run_meta={'spec_name':experiment['name'],'ticker':scenario['company'],'scenario':scenario_label(scenario),'rules_fingerprint':rules_fingerprint(experiment['config']),'scenario_fingerprint':rules_fingerprint(scenario)}
        st.session_state._project.setdefault('evaluations',{})[evaluation_id]={'id':evaluation_id,'experiment_id':experiment['id'],'scenario_id':scenario.get('id'),'result':serializable_result(result)}
        return config,result
    except Exception as exc:
        st.warning(friendly_experiment_error(exc)); return None,None

if page == 'Cenários':
    tab_intro('Cenários'); st.header('Biblioteca de cenários')
    st.caption('O cenário pertence à companhia e descreve somente a estratégia de ordens. Q, H e disclosure são resultados da especificação aplicada, não atributos do cenário.')
    project=st.session_state._project; owner=project.setdefault('scenarios',{'items':{},'active_id':None}); items=owner.setdefault('items',{})
    if not items:
        ids=asset_ids(); create_scenario(project,ids[0] if ids else '', 'Nova estratégia'); reload_project(project,'Primeiro cenário criado.')
    ids=list(items); active_id=owner.get('active_id') if owner.get('active_id') in items else ids[0]
    selected=st.selectbox('Cenário em edição',ids,index=ids.index(active_id),format_func=lambda sid:scenario_label(items[sid]),key='global_scenario_picker')
    if selected!=active_id:
        persist_workspace(); project['scenarios']['active_id']=selected; reload_project(project)
    scenario=items[selected]
    if 'scenario_company_widget' not in st.session_state: st.session_state.scenario_company_widget=scenario.get('company')
    if 'scenario_strategy_widget' not in st.session_state: st.session_state.scenario_strategy_widget=scenario.get('strategy','')
    if 'scenario_description_widget' not in st.session_state: st.session_state.scenario_description_widget=scenario.get('description','')
    st.caption(f"**Editando agora:** {scenario_label(scenario)}")
    controls=st.columns(3)
    if controls[0].button('＋ Novo cenário',type='primary',width='stretch'):
        create_scenario(project,asset_ids()[0] if asset_ids() else '', 'Nova estratégia'); reload_project(project,'Novo cenário criado.')
    if controls[1].button('Duplicar cenário',width='stretch'):
        create_scenario(project,scenario.get('company',''),scenario.get('strategy','Estratégia')+' · cópia',scenario); reload_project(project,'Cenário duplicado.')
    if controls[2].button('Arquivar cenário',width='stretch',disabled=len(items)<=1,help='Remove dos comparadores sem apagar definitivamente. O cenário pode ser restaurado abaixo.'):
        archive_scenario_dialog(selected)
    company_col,strategy_col=st.columns([1,2])
    companies=asset_ids()
    if st.session_state.get('scenario_company_widget') not in companies and companies: st.session_state.scenario_company_widget=companies[0]
    company_col.selectbox('Companhia',companies,key='scenario_company_widget',help='O ticker identifica a companhia e resolve os dados usados em qualquer avaliação deste cenário.')
    strategy_col.text_input('Estratégia',key='scenario_strategy_widget',placeholder='Ex.: acumulação com redução no fechamento')
    st.text_area('Descrição',key='scenario_description_widget',placeholder='Racional econômico ou comportamento que esta trajetória representa.')
    ticker=st.session_state.get('scenario_company_widget')
    reference_price=reference_price_for(ticker)
    price_field=semantic_mapping('reference_price')
    st.caption(f"Preço resolvido pelo campo global `{price_field}`, configurado em **Variáveis → Mapeamentos semânticos**." if price_field else 'Preço de referência ainda não configurado. Defina-o em **Variáveis → Mapeamentos semânticos** ou ao revisar a coluna em **Dados**.')
    price_col,apply_col=st.columns([1,2])
    price_col.metric('Preço de referência',f'{reference_price:,.2f}' if reference_price is not None else '—')
    if apply_col.button('Aplicar preço de referência a todas as ordens',width='stretch',disabled=reference_price is None):
        st.session_state.actions=[{**action,'price':reference_price} for action in st.session_state.actions]; bump_order_editor(selected); persist_workspace(); st.rerun()
    add_buy,add_sell=st.columns(2)
    if add_buy.button('＋ Compra',width='stretch'):
        st.session_state.actions.append({'side':'BUY','quantity':0.0,'price':reference_price or 0.0,'time':'','note':''}); bump_order_editor(selected); persist_workspace(); st.rerun()
    if add_sell.button('＋ Venda',width='stretch'):
        st.session_state.actions.append({'side':'SELL','quantity':0.0,'price':reference_price or 0.0,'time':'','note':''}); bump_order_editor(selected); persist_workspace(); st.rerun()
    rows=[{'Momento':a.get('time',''),'Operação':'Compra' if a.get('side')=='BUY' else 'Venda','Quantidade':a.get('quantity',0.),'Preço':a.get('price',0.),'Observação':a.get('note','')} for a in st.session_state.actions]
    editor_revision=int(st.session_state.get(f'order_editor_revision_{selected}',0))
    editor_key=f'global_scenario_orders_{selected}_{editor_revision}'
    st.data_editor(pd.DataFrame(rows),num_rows='dynamic',hide_index=True,width='stretch',key=editor_key,on_change=sync_scenario_order_editor,args=(selected,editor_key),column_config={
        'Operação':st.column_config.SelectboxColumn('Operação',options=['Compra','Venda'],required=True),
        'Quantidade':st.column_config.NumberColumn('Quantidade',min_value=0.),'Preço':st.column_config.NumberColumn('Preço',min_value=0.)})
    valid_count=len(executable_actions(st.session_state.actions)); incomplete_count=len(st.session_state.actions)-valid_count
    if incomplete_count: st.caption(f'{valid_count} ordem(ns) completa(s) · {incomplete_count} linha(s) ainda em preenchimento.')
    st.caption(f'Nome composto no comparador: **{ticker or "—"} · {st.session_state.get("scenario_strategy_widget") or "Estratégia sem nome"}**. Alterações são salvas automaticamente.')
    st.divider(); st.subheader('Prévia com especificação')
    specification_pool={**project['experiments']['completed'],**project['experiments']['drafts']}
    if specification_pool:
        specification_ids=list(specification_pool); default_spec=project.get('ui',{}).get('scenario_preview_specification_id')
        if default_spec not in specification_ids: default_spec=project.get('active_experiment_id') if project.get('active_experiment_id') in specification_ids else specification_ids[0]
        preview_spec_id=st.selectbox('Especificação aplicada',specification_ids,index=specification_ids.index(default_spec),format_func=lambda eid:f"{specification_pool[eid]['name']} · {'concluída' if specification_pool[eid]['status']=='completed' else 'rascunho'}",key='scenario_preview_specification')
        project.setdefault('ui',{})['scenario_preview_specification_id']=preview_spec_id
        transient_scenario={**scenario,'company':ticker,'strategy':st.session_state.get('scenario_strategy_widget',''),'description':st.session_state.get('scenario_description_widget',''),'actions':list(st.session_state.actions)}
        render_evaluation_preview(specification_pool[preview_spec_id],transient_scenario,'scenario_preview')
    else: st.info('Crie uma especificação para visualizar o comportamento deste cenário.')
    archived=owner.setdefault('archived',{})
    if archived:
        st.divider()
        with st.expander(f'Cenários arquivados ({len(archived)})'):
            st.caption('Arquivamento é reversível e não participa dos comparadores.')
            for archived_id,archived_scenario in list(archived.items()):
                label_col,restore_col=st.columns([5,1])
                label_col.markdown(f"**{scenario_label(archived_scenario)}**")
                if restore_col.button('Restaurar',key=f'restore_scenario_{archived_id}',width='stretch'):
                    restore_scenario(project,archived_id)
                    reload_project(project,'Cenário restaurado e aberto para edição.')

if page == 'Especificações' and experiment_section == 'Visão geral':
    draft=active_draft(st.session_state._project)
    tab_intro('Especificações'); st.header('Especificação em edição')
    st.caption('O rascunho reúne apenas Memória, Capacidade e Intrawindow. Cenários e companhias são independentes e podem ser combinados livremente com esta configuração.')
    if draft:
        name_col,status_col=st.columns([2,1])
        name_col.text_input('Nome da especificação',key='spec_name')
        status_col.metric('Estado','Rascunho')
        config=draft['config']; iw=config['intrawindow']
        summary=pd.DataFrame([
            {'Componente':'Memória','Configuração':f"GAIN {config['memory'].get('GAIN')} · decay {config['memory'].get('LAMBDA')}"},
            {'Componente':'Capacidade','Configuração':f"H₀ gross: {config['capacity'].get('h0_gross_expr') or 'não configurado'}"},
            {'Componente':'Intrawindow','Configuração':f"Q gross {float(iw.get('rho_gross',.5)):.1%} · Q net {float(iw.get('rho_plus',.5)):.1%}/{float(iw.get('rho_minus',.5)):.1%}"},
            {'Componente':'Treasury','Configuração':('Override manual' if iw.get('treasury_override_enabled') else (semantic_mapping('treasury') or 'campo global não selecionado'))},
        ])
        st.dataframe(summary,hide_index=True,width='stretch')
        left,right=st.columns(2)
        if left.button('Fechar editor e voltar ao gerenciador',width='stretch'):
            persist_workspace(); st.session_state._project['active_experiment_id']=None; reload_project(st.session_state._project)
        if right.button('Concluir e congelar especificação',type='primary',width='stretch',help='Congela somente as regras. Avaliações são calculadas automaticamente ao combiná-la com cenários.'):
            persist_workspace(); finalize_active(st.session_state._project); reload_project(st.session_state._project,'Especificação concluída e congelada.')

if page == 'Comparar':
    tab_intro('Comparar'); st.header('Comparar especificações e cenários')
    st.caption('A avaliação é automática. Fixe um dos eixos para isolar o efeito das regras ou da estratégia de ordens.')
    project=st.session_state._project; pool={**project['experiments']['completed'],**project['experiments']['drafts']}; scenarios=project.get('scenarios',{}).get('items',{})
    comparison_modes=['Especificações × um cenário','Cenários × uma especificação']
    saved_ui=project.setdefault('ui',{})
    if st.session_state.get('comparison_mode') not in comparison_modes:
        st.session_state.comparison_mode=saved_ui.get('comparison_mode') if saved_ui.get('comparison_mode') in comparison_modes else comparison_modes[0]
    saved_experiments=[eid for eid in saved_ui.get('comparison_selected_experiment_ids',[]) if eid in pool]
    saved_scenarios=[sid for sid in saved_ui.get('comparison_selected_scenario_ids',[]) if sid in scenarios]
    if 'comparison_selected_experiment_ids' not in st.session_state:
        st.session_state.comparison_selected_experiment_ids=saved_experiments or list(pool)
    else:
        st.session_state.comparison_selected_experiment_ids=[eid for eid in st.session_state.comparison_selected_experiment_ids if eid in pool]
    if 'comparison_selected_scenario_ids' not in st.session_state:
        st.session_state.comparison_selected_scenario_ids=saved_scenarios or list(scenarios)
    else:
        st.session_state.comparison_selected_scenario_ids=[sid for sid in st.session_state.comparison_selected_scenario_ids if sid in scenarios]
    preferred_scenario=saved_ui.get('comparison_fixed_scenario_id') or project.get('scenarios',{}).get('active_id')
    if st.session_state.get('comparison_fixed_scenario_id') not in scenarios:
        st.session_state.comparison_fixed_scenario_id=preferred_scenario if preferred_scenario in scenarios else next(iter(scenarios),None)
    preferred_experiment=saved_ui.get('comparison_fixed_experiment_id') or project.get('active_experiment_id')
    if st.session_state.get('comparison_fixed_experiment_id') not in pool:
        st.session_state.comparison_fixed_experiment_id=preferred_experiment if preferred_experiment in pool else next(iter(pool),None)
    mode=st.radio('Modo de comparação',comparison_modes,horizontal=True,key='comparison_mode')
    experiment_ids=[]; scenario_ids=[]
    if mode=='Especificações × um cenário':
        experiment_ids=st.multiselect('Especificações',list(pool),format_func=lambda eid:pool[eid]['name'],key='comparison_selected_experiment_ids')
        chosen=st.selectbox('Cenário fixo',list(scenarios),format_func=lambda sid:scenario_label(scenarios[sid]),key='comparison_fixed_scenario_id') if scenarios else None
        scenario_ids=[chosen] if chosen else []
    elif mode=='Cenários × uma especificação':
        chosen=st.selectbox('Especificação fixa',list(pool),format_func=lambda eid:pool[eid]['name'],key='comparison_fixed_experiment_id') if pool else None
        experiment_ids=[chosen] if chosen else []
        scenario_ids=st.multiselect('Cenários',list(scenarios),format_func=lambda sid:scenario_label(scenarios[sid]),key='comparison_selected_scenario_ids')
    experiment_ids=[eid for eid in experiment_ids if eid in pool]
    scenario_ids=[sid for sid in scenario_ids if sid in scenarios]
    rows=[]; detail={}; comparison_errors=[]
    for eid in experiment_ids:
        for sid in scenario_ids:
            experiment=pool[eid]; scenario=scenarios[sid]
            try:
                config,outcome=evaluate_pair(experiment,scenario); w=outcome['final_window']
                result_parts=[disclosure_status(outcome['disclosure']),'Execução: '+execution_status(outcome)]
                if outcome['capacity_notices']: result_parts.append(capacity_status(outcome['capacity_notices']))
                status=('Erro: '+outcome['error']) if outcome['error'] else ' · '.join(result_parts)
                intraday_alerts=dimension_labels(sorted(dimension.value for dimension in w.q_crossed))
                net_minus_resolution=outcome.get('capacity_resolution',{}).get('Net−',{})
                rows.append({'Especificação':experiment['name'],'Cenário':scenario_label(scenario),'Companhia':scenario['company'],'Gross final':w.gross,'Net final':w.net,'H net− efetivo':round(net_minus_resolution.get('effective',config.h_minus)),'Utilização gross':w.utilization(CapacityDimension.GROSS),'Alertas intraday':', '.join(intraday_alerts) if intraday_alerts else 'Nenhum','Divulgação no fechamento':disclosure_status(outcome['disclosure']),'Execução':execution_status(outcome),'Capacidade':capacity_status(outcome['capacity_notices']) or 'Dentro de H','Resultado':status})
                detail[(eid,sid)]=(config,outcome)
            except Exception as exc:
                message=friendly_experiment_error(exc)
                rows.append({'Especificação':experiment['name'],'Cenário':scenario_label(scenario),'Companhia':scenario.get('company'),'Gross final':None,'Net final':None,'Utilização gross':None,'Resultado':message.replace('**','')})
                comparison_errors.append(f"**{experiment['name']} × {scenario_label(scenario)}** — {message}")
    if rows:
        results=pd.DataFrame(rows)
        st.dataframe(
            results.drop(columns=['Resultado']),hide_index=True,width='stretch',
            column_config={
                'H net− efetivo':st.column_config.NumberColumn(
                    'H net− efetivo',format='localized',
                    help='Menor valor entre o H net− calculado pela especificação e as ações em tesouraria da companhia. Se houver override experimental explícito, ele substitui a Treasury global.',
                ),
                'Utilização gross':st.column_config.ProgressColumn('Utilização gross',min_value=0.,max_value=1.,format='percent'),
            },
        )
        for comparison_error in comparison_errors:
            st.warning(comparison_error)
        if detail:
            st.subheader('Trajetórias comparadas')
            if mode=='Especificações × um cenário':
                st.caption('Domínio do cenário fixo: o eixo mostra a quantidade de ações. Cada especificação projeta seus próprios Q e H absolutos sobre a mesma trajetória solicitada.')
            else:
                st.caption('Domínio da especificação fixa: cada cenário é normalizado pelo H resolvido para sua companhia. H = 100%; Q é o percentual compartilhado da especificação.')
            options=list(detail)
            mode_key={'Especificações × um cenário':'specs','Cenários × uma especificação':'scenarios'}[mode]
            if mode=='Especificações × um cenário':
                graph_pairs=[(eid,scenario_ids[0]) for eid in experiment_ids] if scenario_ids else []
                chart_context_title=f"Cenário: {scenario_label(scenarios[scenario_ids[0]])}" if scenario_ids else 'Cenário não selecionado'
                series_axis='Especificação'
            elif mode=='Cenários × uma especificação':
                graph_pairs=[(experiment_ids[0],sid) for sid in scenario_ids] if experiment_ids else []
                chart_context_title=f"Especificação: {pool[experiment_ids[0]]['name']}" if experiment_ids else 'Especificação não selecionada'
                series_axis='Cenário'
            graph_pairs=available_comparison_pairs(graph_pairs,detail)
            graph_dimensions=st.multiselect(
                'Dimensões exibidas',['Gross','Net+','Net−'],default=['Gross','Net+'],
                key=f'comparison_graph_dimensions_{mode_key}',
                help='Gross é o volume total negociado. Net+ e Net− são, respectivamente, as exposições líquidas compradora e vendedora.',
            )
            if graph_pairs and graph_dimensions:
                absolute_axis=series_axis=='Especificação'
                trajectory_rows=[]; threshold_rows=[]; rejected_rows=[]
                selected_companies={scenarios[sid]['company'] for _,sid in graph_pairs}
                for eid,sid in graph_pairs:
                    config,outcome=detail[(eid,sid)]
                    full_combination=f"{pool[eid]['name']} × {scenario_label(scenarios[sid])}"
                    if series_axis=='Especificação': series_name=pool[eid]['name']
                    else: series_name=scenario_label(scenarios[sid]) if len(selected_companies)>1 else scenarios[sid]['strategy']
                    dimensions={
                        'Gross':('Gross',config.h_gross,config.rho_gross),
                        'Net+':('Net',config.h_plus,config.rho_plus),
                        'Net−':('Net',config.h_minus,config.rho_minus),
                    }
                    for dimension in graph_dimensions:
                        source,h_value,q_value=dimensions[dimension]
                        threshold_projection=comparison_projection(0.,h_value,q_value,normalized=not absolute_axis)
                        threshold_rows.append({'Série':series_name,'Combinação completa':full_combination,'Especificação':pool[eid]['name'],'Estratégia':scenarios[sid]['strategy'],'Companhia':scenarios[sid]['company'],'Dimensão':dimension,'H absoluto':threshold_projection['h_absolute'],'Q absoluto':threshold_projection['q_absolute'],'Q percentual':threshold_projection['q_ratio']})
                        for _,point in outcome['trajectory'].iterrows():
                            raw=float(point[source])
                            exposure=max(raw,0.) if dimension!='Net−' else max(-raw,0.)
                            projection=comparison_projection(exposure,h_value,q_value,normalized=not absolute_axis)
                            trajectory_rows.append({
                                'Passo':int(point['Passo']),'Série':series_name,'Combinação completa':full_combination,
                                'Especificação':pool[eid]['name'],'Estratégia':scenarios[sid]['strategy'],'Companhia':scenarios[sid]['company'],
                                'Dimensão':dimension,'Quantidade':exposure,'Utilização':projection['utilization'],'Valor no eixo':projection['value'],
                            })
                            if float(point.get('Rejeitada',0.) or 0.)>0 and dimension in str(point.get('Limites','')):
                                requested_raw=float(point['Gross solicitado'] if dimension=='Gross' else point['Net solicitado'])
                                requested_exposure=requested_raw if dimension=='Gross' else (max(requested_raw,0.) if dimension=='Net+' else max(-requested_raw,0.))
                                rejected_rows.append({
                                    'Passo':int(point['Passo']),'Série':series_name,'Especificação':pool[eid]['name'],'Estratégia':scenarios[sid]['strategy'],'Companhia':scenarios[sid]['company'],'Dimensão':dimension,
                                    'Executada':projection['value'],'Solicitada no eixo':comparison_projection(requested_exposure,h_value,q_value,normalized=not absolute_axis)['value'],
                                    'Quantidade solicitada':float(point['Solicitada']),'Quantidade executada':float(point['Quantidade']),'Quantidade rejeitada':float(point['Rejeitada']),'Motivo':'Excederia 100% de H '+dimension,
                                })
                trajectories=pd.DataFrame(trajectory_rows); thresholds=pd.DataFrame(threshold_rows)
                rejected_trajectories=pd.DataFrame(rejected_rows)
                requested_rows=[]
                if absolute_axis and scenario_ids:
                    requested_buy=requested_sell=0.
                    requested_actions=executable_actions(scenarios[scenario_ids[0]].get('actions',[]))
                    requested_states=[(0,requested_buy,requested_sell)]
                    for requested_step,action in enumerate(requested_actions,1):
                        if action.get('side')=='SELL': requested_sell+=float(action.get('quantity',0.) or 0.)
                        else: requested_buy+=float(action.get('quantity',0.) or 0.)
                        requested_states.append((requested_step,requested_buy,requested_sell))
                    for requested_step,buy_total,sell_total in requested_states:
                        requested_net=buy_total-sell_total
                        requested_values={'Gross':buy_total+sell_total,'Net+':max(requested_net,0.),'Net−':max(-requested_net,0.)}
                        for requested_dimension,requested_value in requested_values.items():
                            requested_rows.append({'Passo':requested_step,'Dimensão':requested_dimension,'Quantidade solicitada acumulada':requested_value,'Referência':'Trajetória solicitada pelo cenário'})
                requested_trajectory=pd.DataFrame(requested_rows)
                carry_rows=[]
                comparison_last_step=int(trajectories['Passo'].max()) if not trajectories.empty else 0
                for (_,dimension),group in trajectories.groupby(['Série','Dimensão'],sort=False):
                    last=group.sort_values('Passo').iloc[-1]
                    last_step=int(last['Passo'])
                    if last_step<comparison_last_step:
                        for carry_step in range(last_step,comparison_last_step+1):
                            carry_rows.append({**last.to_dict(),'Passo':carry_step,'Estado':'Sem nova ordem · estado preservado'})
                carried_trajectories=pd.DataFrame(carry_rows)
                legend_rows=[]
                for eid,sid in graph_pairs:
                    config,_=detail[(eid,sid)]
                    saved=pool[eid]['config']; memory=saved['memory']; capacity=saved['capacity']
                    legend_rows.append({
                        'Especificação':pool[eid]['name'],'Cenário':scenario_label(scenarios[sid]),'Companhia':scenarios[sid]['company'],
                        'H gross':round(config.h_gross),'H net+':round(config.h_plus),'H net−':round(config.h_minus),
                        'Q gross (ações)':round(config.h_gross*config.rho_gross),'Q net+ (ações)':round(config.h_plus*config.rho_plus),'Q net− (ações)':round(config.h_minus*config.rho_minus),
                        'Q gross (%)':config.rho_gross,'Q net+ (%)':config.rho_plus,'Q net− (%)':config.rho_minus,
                        'Ganho':float(memory.get('GAIN',0.) or 0.),'Decay':float(memory.get('LAMBDA',0.) or 0.),
                        'Aceleração':float(memory.get('ACCEL',0.) or 0.),'Penalidade reversão':float(memory.get('REV_PENALTY',0.) or 0.),
                        'Hmax':capacity.get('hmax_expr') or '—',
                        'Saturação':f"{capacity.get('sat_kind','—')} · k={float(capacity.get('sat_shape',0.) or 0.):g}",
                    })
                with st.expander('Legenda e parâmetros das trajetórias',expanded=True):
                    legend_frame=pd.DataFrame(legend_rows)
                    if series_axis=='Especificação':
                        legend_frame=legend_frame.drop(columns=['Cenário','Companhia'])
                        st.caption(f"Cenário fixo: **{scenario_label(scenarios[scenario_ids[0]])}**. Cada linha e cada cor abaixo representam uma especificação.")
                    elif series_axis=='Cenário':
                        legend_frame=legend_frame.drop(columns=['Especificação'])
                        st.caption(f"Especificação fixa: **{pool[experiment_ids[0]]['name']}**. Cada linha e cada cor abaixo representam um cenário.")
                    st.dataframe(
                        legend_frame,hide_index=True,width='stretch',
                        column_config={
                            'Especificação':st.column_config.TextColumn(width='large'),
                            'Cenário':st.column_config.TextColumn(width='large'),
                            'Companhia':st.column_config.TextColumn(width='small'),
                            'H gross':st.column_config.NumberColumn(format='localized',width='medium'),
                            'H net+':st.column_config.NumberColumn(format='localized',width='medium'),
                            'H net−':st.column_config.NumberColumn(format='localized',width='medium'),
                            'Q gross (ações)':st.column_config.NumberColumn(format='localized',width='medium'),
                            'Q net+ (ações)':st.column_config.NumberColumn(format='localized',width='medium'),
                            'Q net− (ações)':st.column_config.NumberColumn(format='localized',width='medium'),
                            'Q gross (%)':st.column_config.NumberColumn(format='percent'),
                            'Q net+ (%)':st.column_config.NumberColumn(format='percent'),
                            'Q net− (%)':st.column_config.NumberColumn(format='percent'),
                            'Ganho':st.column_config.NumberColumn(format='%.2f',width='small'),
                            'Decay':st.column_config.NumberColumn(format='%.2f',width='small'),
                            'Aceleração':st.column_config.NumberColumn(format='%.2f',width='small'),
                            'Penalidade reversão':st.column_config.NumberColumn(format='%.2f',width='small'),
                            'Hmax':st.column_config.TextColumn(width='medium'),
                            'Saturação':st.column_config.TextColumn(width='medium'),
                        },
                    )
                for dimension in graph_dimensions:
                    st.markdown(f'##### {dimension}')
                    dimension_data=trajectories[trajectories['Dimensão']==dimension]
                    dimension_q=thresholds[thresholds['Dimensão']==dimension]
                    dimension_rejected=rejected_trajectories[rejected_trajectories['Dimensão']==dimension] if not rejected_trajectories.empty else pd.DataFrame([])
                    dimension_carried=carried_trajectories[carried_trajectories['Dimensão']==dimension] if not carried_trajectories.empty else pd.DataFrame([])
                    dimension_carried_end=dimension_carried[dimension_carried['Passo']==comparison_last_step] if not dimension_carried.empty else pd.DataFrame([])
                    max_step=max(int(dimension_data['Passo'].max()),1)
                    combination_order=list(dict.fromkeys(dimension_data['Série'].tolist()))
                    palette=['#4C78A8','#F58518','#E45756','#72B7B2','#54A24B','#EECA3B','#B279A2','#FF9DA6','#9D755D','#BAB0AC']
                    color_scale=alt.Scale(domain=combination_order,range=[palette[index%len(palette)] for index in range(len(combination_order))])
                    legend_config=alt.Legend(title=['Clique para destacar','Shift + clique seleciona várias'],labelLimit=0)
                    focus=alt.selection_point(fields=['Série'],bind='legend',empty=True)
                    y_axis=alt.Axis(format='~s') if absolute_axis else alt.Axis(format='%')
                    y_title='Quantidade de ações' if absolute_axis else 'Utilização de H'
                    base=alt.Chart(dimension_data).encode(
                        x=alt.X('Passo:Q',scale=alt.Scale(domain=[0,max_step]),axis=alt.Axis(tickMinStep=1)),
                        y=alt.Y('Valor no eixo:Q',axis=y_axis,title=y_title),
                        tooltip=['Passo:Q','Série:N','Especificação:N','Estratégia:N','Companhia:N',alt.Tooltip('Quantidade:Q',format=',.0f'),alt.Tooltip('Utilização:Q',format='.1%')],
                    )
                    if absolute_axis:
                        lines=base.mark_line(strokeWidth=3,color='#e4e7ee').interactive(bind_x=False,bind_y=True)
                        points=base.mark_point(size=85,filled=True,color='#e4e7ee')
                    else:
                        lines=base.mark_line(strokeWidth=3).encode(
                            color=alt.Color('Série:N',scale=color_scale,legend=legend_config),
                            opacity=alt.condition(focus,alt.value(1.),alt.value(.15)),
                        ).add_params(focus).interactive(bind_x=False,bind_y=True)
                        points=base.mark_point(size=85,filled=True).encode(
                            color=alt.Color('Série:N',scale=color_scale,legend=None),
                            opacity=alt.condition(focus,alt.value(1.),alt.value(.15)),
                        )
                    hover_targets=base.mark_point(size=700,opacity=.001).encode(
                        color=alt.Color('Série:N',scale=color_scale,legend=None),
                    )
                    carried_lines=carried_endpoints=None
                    if not dimension_carried.empty:
                        carried_line_mark=alt.Chart(dimension_carried).mark_line(strokeDash=[8,5],strokeWidth=3,color='#e4e7ee') if absolute_axis else alt.Chart(dimension_carried).mark_line(strokeDash=[8,5],strokeWidth=3)
                        carried_lines=carried_line_mark.encode(
                            x=alt.X('Passo:Q',scale=alt.Scale(domain=[0,max_step]),axis=alt.Axis(tickMinStep=1)),
                            y=alt.Y('Valor no eixo:Q',axis=y_axis,title=y_title),
                            color=alt.value('#e4e7ee') if absolute_axis else alt.Color('Série:N',scale=color_scale,legend=None),
                            opacity=alt.value(.90) if absolute_axis else alt.condition(focus,alt.value(.90),alt.value(.10)),
                            tooltip=['Passo:Q','Série:N','Especificação:N','Estratégia:N','Companhia:N','Estado:N',alt.Tooltip('Quantidade:Q',format=',.0f'),alt.Tooltip('Utilização:Q',format='.1%')],
                        )
                        carried_endpoint_mark=alt.Chart(dimension_carried_end).mark_point(size=100,filled=False,strokeWidth=3,color='#e4e7ee') if absolute_axis else alt.Chart(dimension_carried_end).mark_point(size=100,filled=False,strokeWidth=3)
                        carried_endpoints=carried_endpoint_mark.encode(
                            x=alt.X('Passo:Q',scale=alt.Scale(domain=[0,max_step]),axis=alt.Axis(tickMinStep=1)),
                            y=alt.Y('Valor no eixo:Q',axis=y_axis,title=y_title),
                            color=alt.value('#e4e7ee') if absolute_axis else alt.Color('Série:N',scale=color_scale,legend=None),
                            opacity=alt.value(.90) if absolute_axis else alt.condition(focus,alt.value(.90),alt.value(.10)),
                            tooltip=['Passo:Q','Série:N','Estado:N',alt.Tooltip('Quantidade:Q',format=',.0f'),alt.Tooltip('Utilização:Q',format='.1%')],
                        )
                    if series_axis=='Cenário':
                        # A specification is fixed in this view, so Q is one protocol
                        # reference shared by every scenario rather than a trajectory.
                        shared_q=dimension_q.iloc[[0]].assign(Referência='Q compartilhado pela especificação')
                        q_rules=alt.Chart(shared_q).mark_rule(color='#EECA3B',strokeDash=[6,4],strokeWidth=4).encode(
                            y='Q percentual:Q',tooltip=['Referência:N','Especificação:N',alt.Tooltip('Q percentual:Q',format='.1%')],
                        )
                        q_hover_targets=alt.Chart(shared_q).mark_rule(strokeWidth=18,opacity=.001).encode(
                            y='Q percentual:Q',tooltip=['Referência:N','Especificação:N',alt.Tooltip('Q percentual:Q',format='.1%')],
                        )
                        hard_cap_data=pd.DataFrame([{'H percentual':1.,'Referência':'H compartilhado pela especificação'}])
                        hard_cap=alt.Chart(hard_cap_data).mark_rule(color='#ff4b4b',strokeWidth=2).encode(
                            y=alt.Y('H percentual:Q',title=y_title),tooltip=['Referência:N',alt.Tooltip('H percentual:Q',format='.0%')],
                        )
                    else:
                        q_rules=alt.Chart(dimension_q).mark_rule(strokeDash=[6,4],strokeWidth=4).encode(
                            y='Q absoluto:Q',color=alt.Color('Série:N',scale=color_scale,legend=legend_config),opacity=alt.condition(focus,alt.value(.9),alt.value(.10)),
                            tooltip=['Série:N','Especificação:N',alt.Tooltip('Q absoluto:Q',format=',.0f'),alt.Tooltip('Q percentual:Q',format='.1%')],
                        ).add_params(focus)
                        q_hover_targets=alt.Chart(dimension_q).mark_rule(strokeWidth=18,opacity=.001).encode(
                            y='Q absoluto:Q',color=alt.Color('Série:N',scale=color_scale,legend=None),
                            tooltip=['Série:N','Especificação:N',alt.Tooltip('Q absoluto:Q',format=',.0f'),alt.Tooltip('Q percentual:Q',format='.1%')],
                        )
                        hard_cap=alt.Chart(dimension_q).mark_rule(strokeWidth=2).encode(
                            y=alt.Y('H absoluto:Q',title=y_title),color=alt.Color('Série:N',scale=color_scale,legend=None),opacity=alt.condition(focus,alt.value(.75),alt.value(.08)),
                            tooltip=['Série:N','Especificação:N',alt.Tooltip('H absoluto:Q',format=',.0f')],
                        )
                    rejected_connector=rejected_points=None
                    if not dimension_rejected.empty:
                        rejected_connector=alt.Chart(dimension_rejected).mark_rule(color='#ff4b4b',strokeDash=[4,3],strokeWidth=3).encode(x='Passo:Q',y='Executada:Q',y2='Solicitada no eixo:Q')
                        rejected_tooltip=['Série:N','Especificação:N','Estratégia:N','Motivo:N',alt.Tooltip('Quantidade solicitada:Q',format=',.0f'),alt.Tooltip('Quantidade executada:Q',format=',.0f'),alt.Tooltip('Quantidade rejeitada:Q',format=',.0f')]
                        rejected_points=alt.Chart(dimension_rejected).mark_point(shape='cross',size=220,strokeWidth=4,color='#ff4b4b').encode(x='Passo:Q',y='Solicitada no eixo:Q',tooltip=rejected_tooltip)
                    chart_layers=[hard_cap,lines,points,hover_targets]
                    if absolute_axis and not requested_trajectory.empty:
                        dimension_requested=requested_trajectory[requested_trajectory['Dimensão']==dimension]
                        requested_line=alt.Chart(dimension_requested).mark_line(color='#7f8591',strokeDash=[3,3],strokeWidth=2).encode(
                            x=alt.X('Passo:Q',scale=alt.Scale(domain=[0,max_step]),axis=alt.Axis(tickMinStep=1)),
                            y=alt.Y('Quantidade solicitada acumulada:Q',axis=y_axis,title=y_title),
                            tooltip=['Passo:Q','Referência:N',alt.Tooltip('Quantidade solicitada acumulada:Q',format=',.0f')],
                        )
                        chart_layers.insert(0,requested_line)
                    if not dimension_carried.empty:
                        chart_layers.extend([carried_lines,carried_endpoints])
                    chart_layers.extend([q_rules,q_hover_targets])
                    if not dimension_rejected.empty:
                        chart_layers.extend([rejected_connector,rejected_points])
                    comparison_chart=alt.layer(*chart_layers).properties(title=chart_context_title,height=320).resolve_scale(color='independent')
                    st.altair_chart(comparison_chart,width='stretch')
                    if absolute_axis:
                        st.caption('Cinza pontilhado: trajetória solicitada. Linha clara contínua: execução, mantida neutra porque a referência é o mesmo cenário. Q tracejado e H contínuo usam a cor da especificação. Vermelho e ×: parcela rejeitada.')
                    else:
                        st.caption('Linhas coloridas: utilização de H por cenário. Q tracejado é compartilhado; H = 100%. Valores absolutos permanecem na legenda e nos tooltips. Vermelho e ×: parcela rejeitada.')
            else:
                st.info('Selecione ao menos uma combinação e uma dimensão para montar o comparativo gráfico.')
            st.divider()
            options=list(detail); selected_pair=st.selectbox('Abrir avaliação detalhada',options,format_func=lambda pair:f"{pool[pair[0]]['name']} × {scenario_label(scenarios[pair[1]])}")
            st.subheader('Detalhamento da combinação')
            render_evaluation_preview(pool[selected_pair[0]],scenarios[selected_pair[1]],'compare_detail')
    else: st.info('Selecione ao menos uma combinação válida.')

if page == 'Especificações' and (experiment_section == 'Gerenciar' or not active_draft(st.session_state._project)):
    tab_intro('Especificações'); st.header('Gerenciar especificações')
    st.caption('Rascunhos têm autosave e histórico próprio. Uma especificação concluída pode ser reaberta para correção ou duplicada para criar uma alternativa.')
    project=st.session_state._project; drafts=project['experiments']['drafts']; completed=project['experiments']['completed']
    all_sources={**completed,**drafts}
    source_id=st.selectbox('Usar configuração existente como base', ['— em branco —']+list(all_sources),format_func=lambda eid:'— em branco —' if eid=='— em branco —' else all_sources[eid]['name'])
    new_name=st.text_input('Nome da nova especificação',placeholder='Ex.: limite de posição com Treasury')
    if st.button('Criar especificação',type='primary',width='stretch'):
        source=None if source_id=='— em branco —' else all_sources[source_id]
        create_draft(project,new_name.strip() or 'Nova especificação',source); reload_project(project,'Nova especificação criada.')
    st.subheader('Rascunhos')
    if not drafts: st.caption('Nenhum rascunho.')
    for eid,item in list(drafts.items()):
        a,b,c,d=st.columns([4,1,1,1]); a.markdown(f"**{item['name']}**  \nAtualizado: {item.get('updated_at','')[:19]}")
        if b.button('Abrir',key=f'open_{eid}',width='stretch'): project['active_experiment_id']=eid; reload_project(project)
        if c.button('Duplicar',key=f'dup_{eid}',width='stretch'): duplicate_as_draft(project,item); reload_project(project)
        if d.button('Arquivar',key=f'del_{eid}',width='stretch'): delete_experiment(project,eid); reload_project(project)
    st.subheader('Concluídos')
    if not completed: st.caption('Nenhuma especificação concluída.')
    for eid,item in list(completed.items()):
        a,b,c,d,e=st.columns([4,1,1,1,1]); a.markdown(f"**{item['name']}** · `{item.get('fingerprint','')}`  \nConcluído: {item.get('completed_at','')[:19]}")
        if b.button('Ver',key=f'view_{eid}',width='stretch'): project.setdefault('ui',{})['view_completed_id']=eid; reload_project(project)
        if c.button('Editar',key=f'edit_{eid}',width='stretch'): reopen_completed(project,eid); reload_project(project,'Especificação reaberta para edição.')
        if d.button('Duplicar',key=f'clone_{eid}',width='stretch'): duplicate_as_draft(project,item); reload_project(project)
        if e.button('Arquivar',key=f'archive_{eid}',width='stretch'): delete_experiment(project,eid); reload_project(project)
    viewed_id=project.get('ui',{}).get('view_completed_id'); viewed=completed.get(viewed_id)
    if viewed:
        st.divider(); st.subheader('Snapshot concluído · '+viewed['name'])
        st.caption(f"Fingerprint `{viewed.get('fingerprint','')}` · motor {viewed.get('engine_version','—')} · somente leitura")
        cfg=viewed['config']; iw=cfg['intrawindow']
        st.dataframe(pd.DataFrame([
            {'Componente':'Sinal', 'Definição':cfg['memory'].get('signal_expr')},
            {'Componente':'Atualização', 'Definição':cfg['memory'].get('update_expr')},
            {'Componente':'H₀ gross', 'Definição':cfg['capacity'].get('h0_gross_expr')},
            {'Componente':'Hmax', 'Definição':cfg['capacity'].get('hmax_expr')},
            {'Componente':'Q', 'Definição':f"Gross {float(iw.get('rho_gross',.5)):.1%} · Net+ {float(iw.get('rho_plus',.5)):.1%} · Net− {float(iw.get('rho_minus',.5)):.1%}"},
            {'Componente':'Treasury', 'Definição':'override manual' if iw.get('treasury_override_enabled') else (semantic_mapping('treasury') or 'campo global não selecionado')},
        ]),hide_index=True,width='stretch')
        st.caption('Resultados são avaliações independentes, calculadas automaticamente ao combinar este snapshot com um cenário.')

if page == 'Especificações' and active_draft(st.session_state._project):
    st.divider(); st.subheader('Prévia com cenário')
    st.caption('Troque livremente o cenário usado na prévia. Essa escolha é apenas de interface e não altera a especificação nem seu histórico.')
    project=st.session_state._project; scenarios=project.get('scenarios',{}).get('items',{})
    if scenarios:
        scenario_ids=list(scenarios); default_scenario=project.get('ui',{}).get('specification_preview_scenario_id')
        if default_scenario not in scenario_ids: default_scenario=project.get('scenarios',{}).get('active_id') if project.get('scenarios',{}).get('active_id') in scenario_ids else scenario_ids[0]
        preview_scenario_id=st.selectbox('Cenário aplicado',scenario_ids,index=scenario_ids.index(default_scenario),format_func=lambda sid:scenario_label(scenarios[sid]),key='specification_preview_scenario')
        project.setdefault('ui',{})['specification_preview_scenario_id']=preview_scenario_id
        draft=active_draft(project); transient_experiment={**draft,'name':st.session_state.get('spec_name',draft['name']),'config':experiment_payload()}
        render_evaluation_preview(transient_experiment,scenarios[preview_scenario_id],'specification_preview')
    else: st.info('Crie um cenário para visualizar o comportamento desta especificação.')

# Widget edits are working-state changes. Persisting at the end makes them survive a
# Streamlit process restart without turning every individual field into a save flow.
try:
    persist_workspace()
except OSError as exc:
    st.warning(f'Não foi possível persistir o rascunho local: {exc}')
