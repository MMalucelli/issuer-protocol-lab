import pytest
from issuer_lab.capacity_builder import MarketMetrics,H0Rule,HRule

def test_h0_from_adv():
    m=MarketMetrics('X',1_000_000,10,10_000_000,10_000_000,.3)
    assert H0Rule(rate=.01).build(m)==(10_000,10_000,10_000)

def test_h_is_bounded():
    r=HRule(hmax_expression='H0 * 4',signal_expression='clamp(I * 2,0,1)')
    assert r.capacity(100,{'I':0})==100
    assert r.capacity(100,{'I':100})<=400

def test_decay_reduces_information():
    r=HRule(decay_expression='I * exp(-LAMBDA * DT)')
    assert r.decay(1,1,{'LAMBDA':.5})<1

def test_reversal_degrades_state():
    r=HRule(info_update_expression='I_DECAYED * (1 - REV * REV_PENALTY)')
    p={'LAMBDA':0.,'REV_PENALTY':.5}
    assert r.update_information(1,0,1,True,p)<r.update_information(1,0,1,False,p)

def test_information_update_can_reference_signal():
    r=HRule(signal_expression='clamp(U,0,1)', info_update_expression='I_DECAYED + SIGNAL * 0.5')
    out=r.update_information(0.0,0.8,1,False,{'LAMBDA':0.0})
    assert out == pytest.approx(0.4)
