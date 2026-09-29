from issuer_lab.data_sources import SourceSpec, resolve_observation, _path

def test_json_path():
    assert _path({'a':[{'b':3}]},'a.0.b') == 3

def test_snapshot_observation_provenance():
    o=resolve_observation(SourceSpec('ADV',unit='ações/dia',scale=.5),'PETR4',{'ADV':100},now='t')
    assert o.value==50 and o.source=='market_snapshot.json' and o.fetched_at=='t'

def test_manual_source():
    o=resolve_observation(SourceSpec('X',provider='Manual',manual_value=2.5,scale=2),'PETR4',{},now='t')
    assert o.value==5

def test_generic_endpoint_template_variables():
    from issuer_lab.data_sources import render_template
    assert render_template('https://x/{region}/{exchange}/{ticker}', 'PETR4', {'region':'BR','exchange':'BVMF'}) == 'https://x/BR/BVMF/PETR4'


def test_unknown_template_variable_is_explicit_error():
    import pytest
    from issuer_lab.data_sources import render_template
    with pytest.raises(ValueError, match='placeholder sem valor'):
        render_template('https://x/{suffix}/{ticker}', 'PETR4', {})

def test_local_json_keyed_records(tmp_path):
    import json
    from issuer_lab.data_sources import test_local_source, SourceSpec
    (tmp_path/'x.json').write_text(json.dumps({'stocks':{'PETR4':{'metrics':{'adv':123}}}}),encoding='utf-8')
    s=SourceSpec('ADV',provider='Arquivo local',field='metrics.adv',local_file='x.json',collection='stocks')
    r=test_local_source(s,'PETR4',tmp_path)
    assert r['value']==123 and r['record_id']=='PETR4'

def test_local_csv_record_lookup(tmp_path):
    from issuer_lab.data_sources import test_local_source, SourceSpec
    (tmp_path/'x.csv').write_text('ticker,value\nPETR4,42\nVALE3,9\n',encoding='utf-8')
    s=SourceSpec('X',provider='Arquivo local',field='value',local_file='x.csv',identifier_field='ticker')
    assert test_local_source(s,'VALE3',tmp_path)['value']==9
