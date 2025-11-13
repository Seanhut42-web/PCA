import io, pandas as pd

def export_labels_basic(returns: pd.DataFrame, regime: pd.Series) -> bytes:
    idx = returns.index.intersection(regime.index); reg = regime.reindex(idx); risk = reg.isin({'Goldilocks','Reflation'}).astype('boolean')
    df = pd.DataFrame({'Date':idx,'Regime':reg.values,'Risk_On':risk.values})
    buf=io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Labels')
        (returns[['HY','IG']].groupby(reg).mean()).to_excel(w, sheet_name='AvgByRegime')
        (returns[['HY','IG']].groupby(risk).mean()).to_excel(w, sheet_name='AvgByRisk')
    buf.seek(0); return buf.read()

def export_labels_strategy(returns: pd.DataFrame, regime: pd.Series) -> bytes:
    idx = returns.index.intersection(regime.index); ret=returns[['HY','IG']].reindex(idx).copy(); reg=regime.reindex(idx)
    risk=reg.isin({'Goldilocks','Reflation'}).astype('boolean'); sig=reg.shift(1)
    hy=sig.isin({'Goldilocks','Reflation'}).astype(float); ig=1.0-hy
    sleeve=(hy==1.0).map({True:'HY',False:'IG'})
    strat=hy*ret['HY']+ig*ret['IG']
    out=pd.DataFrame({'Date':idx,'Regime':reg.values,'Risk_On':risk.values,'Sleeve':sleeve.values,'HY_Return':ret['HY'].values,'IG_Return':ret['IG'].values,'Strategy_Return':strat.values})
    if 'EMBI' in returns.columns: out['EMBI_Return']=returns['EMBI'].reindex(idx).values
    buf=io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        out.to_excel(w, index=False, sheet_name='Labels_And_Strategy')
        (ret.groupby(reg).mean()).to_excel(w, sheet_name='AvgByRegime_HY_IG')
        (ret.groupby(risk)[['HY','IG']].mean()).to_excel(w, sheet_name='AvgByRisk_HY_IG')
    buf.seek(0); return buf.read()
