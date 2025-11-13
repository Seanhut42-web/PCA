import numpy as np, pandas as pd

def calendar_returns(strat: pd.Series, bench: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({'Strategy':strat,'EMBI GD':bench}).dropna().sort_index(); df['Year']=df.index.year
    return df.groupby('Year').apply(lambda x: (1+x[['Strategy','EMBI GD']]).prod()-1)

def rolling_excess(strat, bench, window=12):
    rs=(1+strat).rolling(window).apply(np.prod, raw=False); rb=(1+bench).rolling(window).apply(np.prod, raw=False)
    return (rs/rb)-1

def cumulative_excess(strat, bench):
    cs=(1+strat).cumprod(); cb=(1+bench).cumprod(); return (cs/cb)-1

def rolling_te_ir(strat, bench, window=12):
    df=pd.DataFrame({'Strategy':strat,'EMBI GD':bench}).dropna().sort_index(); act=df['Strategy']-df['EMBI GD']
    te_roll=act.rolling(window).std()*np.sqrt(12); te_over=act.std()*np.sqrt(12)
    roll_active=(1+act).rolling(window).apply(np.prod, raw=False)-1; ir_roll=roll_active/te_roll
    ann_s=df['Strategy'].mean()*12; ann_b=df['EMBI GD'].mean()*12
    ir_over=(ann_s-ann_b)/te_over if te_over else float('nan')
    return te_roll, te_over, ir_roll, ir_over, ann_s, ann_b
