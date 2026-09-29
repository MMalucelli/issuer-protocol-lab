import pandas as pd
from pathlib import Path
from issuer_lab.relational_sources import eval_reference, join_snapshot, inspect_snapshot, validate_unique_name, provenance_description

def test_reference_language():
    r={'symbol':'PETR4.SA','exchange':'B3'}
    assert eval_reference('LEFT(5, [symbol])',r)=='PETR4'
    assert eval_reference('CONCAT(LEFT(5, [symbol]), ".", [exchange])',r)=='PETR4.B3'

def test_join_and_case_insensitive_names():
    b=pd.DataFrame({'main_id':['PETR4','VALE3'],'ADV':[1,2]})
    s=pd.DataFrame({'symbol':['PETR4.SA','VALE3.SA'],'treasury':[10,20]})
    out,stats=join_snapshot(b,s,'[main_id]','LEFT(5, [symbol])',{'treasury':'TREASURY'})
    assert out.TREASURY.tolist()==[10,20] and stats['matched']==2
    try: validate_unique_name('adv',list(out.columns)); assert False
    except ValueError: pass

def test_provenance_description_prefers_user_text_and_has_source_fallback():
    meta={'source':'market_snapshot.json','field':'metrics.adv','description':'Volume médio diário'}
    assert provenance_description(meta)=='Volume médio diário'
    assert provenance_description({**meta,'description':''})=='Fonte: market_snapshot.json · metrics.adv'

def test_join_multiple_selected_columns_normalizes_destination_names():
    base=pd.DataFrame({'main_id':['PETR4','VALE3']})
    source=pd.DataFrame({
        'symbol':['PETR4.SA','VALE3.SA'],
        'treasury_shares':[100,200],
        'free_float_shares':[1000,2000],
        'reference_date':['2026-09-01','2026-09-01'],
    })
    selected={
        'treasury_shares':'treasury_shares',
        'free_float_shares':'free_float_shares',
        'reference_date':'reference_date',
    }
    out,stats=join_snapshot(base,source,'[main_id]','LEFT(5, [symbol])',selected)
    assert stats['matched']==2
    assert out.columns.tolist()==[
        'main_id','TREASURY_SHARES','FREE_FLOAT_SHARES','REFERENCE_DATE'
    ]
    assert out.loc[0,'TREASURY_SHARES']==100
    assert out.loc[1,'FREE_FLOAT_SHARES']==2000
from issuer_lab.relational_sources import build_base_snapshot, add_manual_base_ids, visible_base, canonical_base_columns

def test_base_snapshot_tracks_import_vs_manual_and_preserves_manual():
    src=pd.DataFrame({'symbol':['PETR4.SA','VALE3.SA']})
    base=build_base_snapshot(src,'LEFT(5, [symbol])',origin='yahoo.json · root')
    assert base.main_id.tolist()==['PETR4','VALE3']
    assert set(base.__base_origin__)=={'import'}
    base=add_manual_base_ids(base,['KEPL3'])
    assert base.loc[base.main_id=='KEPL3','__base_origin__'].iloc[0]=='manual'
    replacement=pd.DataFrame({'symbol':['ITUB4.SA']})
    manual=base.loc[base.__base_origin__=='manual']
    new=build_base_snapshot(replacement,'LEFT(5, [symbol])',origin='new.json · root',existing_manual=manual)
    assert new.main_id.tolist()==['ITUB4','KEPL3']
    assert visible_base(new).columns.tolist()==['main_id']

def test_main_id_is_always_the_first_public_base_column():
    legacy=pd.DataFrame([{'ADV':10,'TREASURY':2,'main_id':'PETR4','__base_origin__':'import'}])
    canonical=canonical_base_columns(legacy)
    assert canonical.columns.tolist()==['main_id','ADV','TREASURY','__base_origin__']
    assert visible_base(legacy).columns.tolist()==['main_id','ADV','TREASURY']
