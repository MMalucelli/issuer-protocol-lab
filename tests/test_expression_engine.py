import math
from issuer_lab.expression_engine import evaluate, endpoint_saturation, evaluate_derived, direct_dependents
from issuer_lab.capacity_builder import HRule

def test_safe_expression():
    assert evaluate('sqrt(X) + 2 ** 3', {'X':9}) == 11

def test_hyperbolic_reaches_endpoint():
    assert endpoint_saturation(1.0,'hyperbolic',3.0) == 1.0

def test_exponential_reaches_endpoint():
    assert abs(endpoint_saturation(1.0,'exponential',3.0)-1.0)<1e-12

def test_decay_families_are_expressions():
    e=evaluate('I * exp(-LAMBDA * DT)',{'I':1,'LAMBDA':.2,'DT':2})
    l=evaluate('max(I - LAMBDA * DT, 0)',{'I':1,'LAMBDA':.2,'DT':2})
    h=evaluate('I / (1 + LAMBDA * DT)',{'I':1,'LAMBDA':.2,'DT':2})
    assert e!=l and h!=l

def test_unused_text_and_date_fields_do_not_break_numeric_formulas():
    values=evaluate_derived(
        {'CAPACITY':'ADV * 0.01'},
        {'ADV':1_000_000,'REFERENCE_DATE':'2026-09-18','SECTOR':'Energy'},
    )
    assert values['CAPACITY']==10_000
    assert values['REFERENCE_DATE']=='2026-09-18'

def test_referenced_non_numeric_field_has_contextual_error():
    import pytest
    with pytest.raises(ValueError,match='REFERENCE_DATE precisa ser numérica'):
        evaluate_derived({'X':'REFERENCE_DATE + 1'},{'REFERENCE_DATE':'2026-09-18'})

def test_dependent_lookup_survives_unrelated_invalid_formula():
    defs={'LIQUIDITY':'TURNOVER / FLOAT','BROKEN':'1 +','LIMIT':'LIQUIDITY * 2'}
    assert direct_dependents(defs,'LIQUIDITY')==['LIMIT']
    assert direct_dependents(defs,'BROKEN')==[]

def test_h_rule_hits_hmax_at_signal_one():
    r=HRule(hmax_expression='H0 * 5',signal_expression='clamp(I,0,1)',saturation='hyperbolic')
    assert r.capacity(100,{'I':1}) == 500
