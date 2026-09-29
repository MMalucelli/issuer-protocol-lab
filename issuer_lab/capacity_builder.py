from __future__ import annotations
from dataclasses import dataclass
from .expression_engine import evaluate, endpoint_saturation

@dataclass(frozen=True)
class MarketMetrics:
    ticker:str; adv:float; price:float; float_shares:float|None; turnover_brl:float; volatility:float

@dataclass(frozen=True)
class FormulaRule:
    expression:str
    def evaluate(self,variables:dict[str,float])->float: return evaluate(self.expression,variables)

@dataclass(frozen=True)
class HRule:
    hmax_expression:str='H0 * 5'
    signal_expression:str='clamp(I * I_MULT, 0, 1)'
    decay_expression:str='I * exp(-LAMBDA * DT)'
    info_update_expression:str='I_DECAYED + U * GAIN * (1 + ACCEL * max(STREAK - 1, 0))'
    saturation:str='hyperbolic'
    saturation_shape:float=3.0
    def hmax(self,h0:float,extra:dict[str,float]|None=None)->float:
        v={'H0':h0,**(extra or {})}; return max(h0,evaluate(self.hmax_expression,v))
    def decay(self,information:float,periods:float,params:dict[str,float])->float:
        return max(0.0,evaluate(self.decay_expression,{'I':information,'DT':periods,**params}))
    def signal(self,variables:dict[str,float])->float:
        return max(0.0,min(1.0,evaluate(self.signal_expression,variables)))
    def capacity(self,h0:float,variables:dict[str,float])->float:
        hm=self.hmax(h0,variables); s=endpoint_saturation(self.signal(variables),self.saturation,self.saturation_shape)
        return h0+s*(hm-h0)
    def update_information(self,information:float,utilization:float,streak:int,reversed_direction:bool,params:dict[str,float])->float:
        dec=self.decay(information,1.0,params)
        v={'I':information,'I_DECAYED':dec,'U':utilization,'STREAK':float(streak),'REV':1.0 if reversed_direction else 0.0,'I_MULT':1.0,**params}
        v['SIGNAL']=self.signal(v)
        return max(0.0,min(1.0,evaluate(self.info_update_expression,v)))

# Backward-compatible helper retained only for old unit tests / migrations.
@dataclass(frozen=True)
class H0Rule:
    base:str='ADV'; rate:float=.01; gross_multiplier:float=1.; plus_multiplier:float=1.; minus_multiplier:float=1.
    def base_shares(self,m:MarketMetrics)->float:
        if self.base=='ADV': return m.adv
        if self.base=='FLOAT': return float(m.float_shares or 0.)
        if self.base=='TURNOVER': return 0. if m.price<=0 else m.turnover_brl/m.price
        raise ValueError(f'unknown H0 base: {self.base}')
    def build(self,m:MarketMetrics):
        b=max(self.base_shares(m)*self.rate,0.); g=b*self.gross_multiplier; p=b*self.plus_multiplier; n=b*self.minus_multiplier
        return max(g,p,n),p,n
