import json
import pytest
from issuer_lab.expression_engine import dependency_graph, dependency_layers, explain_dependency
from issuer_lab.specification import LabSpecification


def test_dependency_explanation_resolves_intermediate_concepts():
    defs={'LIQ':'TURNOVER / FLOAT','I_MARKET':'clamp(VOL * LIQ, 0, 1)'}
    prim={'TURNOVER':100.0,'FLOAT':50.0,'VOL':0.2}
    rows=explain_dependency('I_MARKET',defs,prim)
    by_name={r['name']:r for r in rows}
    assert by_name['LIQ']['value']==2.0
    assert by_name['I_MARKET']['value']==pytest.approx(0.4)
    assert by_name['VOL']['kind']=='dado primitivo'
    assert dependency_layers('I_MARKET',defs,set(prim))[0]==['I_MARKET']


def test_dependency_graph_rejects_unknown_and_cycle():
    with pytest.raises(ValueError): dependency_graph({'A':'B + 1'},{'X'})
    with pytest.raises(ValueError): dependency_graph({'A':'B + 1','B':'A + 1'},set())


def test_specification_roundtrip_is_stable():
    s=LabSpecification('x',{'base_table':[{'main_id':'X','ADV':100}]},[{'Nome':'L','Função':'ADV'}],{'signal':'U'},{'h0':'ADV*.01'},{'h':1},[{'side':'BUY','quantity':1,'price':2}])
    restored=LabSpecification.from_json(s.to_json())
    assert restored.to_dict()==s.to_dict()
    assert json.loads(restored.to_json())['schema_version']==2
