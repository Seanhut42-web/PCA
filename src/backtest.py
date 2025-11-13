import numpy as np, pandas as pd

def drawdown(r: pd.Series) -> pd.Series:
    c=(1+r).cumprod(); return c/c.cummax()-1

def hy_ig_strategy(returns: pd.DataFrame, regime: pd.Series):
    idx = returns.index.intersection(regime.index)
    ret = returns.loc[idx]; reg = regime.loc[idx]
    sig = reg.shift(1)
    wHY = sig.isin(['Goldilocks','Reflation']).astype(float); wIG = 1.0-wHY
    strat = wHY*ret['HY'] + wIG*ret['IG']; bench = ret['EMBI']
    return {'strat_ret': strat,'bench_ret': bench,'cum_strat': (1+strat).cumprod(),'cum_bench': (1+bench).cumprod(),'dd_strat': drawdown(strat),'dd_bench': drawdown(bench)}
