import numpy as np, pandas as pd
from sklearn.decomposition import PCA

EQUITY_CANDIDATES = ['MSCI World','SPX Index','SXXP Index','MXEF Index','HSI Index','TPX Index']
YIELD_CANDIDATES  = ['USGG10Y Index','USGG10YR Index','USGG10','US10Y','GUKG10 Index','GTDEM10Y Govt']

def _anchor(Z, cands):
    for c in cands:
        if c in Z.columns: return c
    return Z.columns[0]

def expanding_pca_2(Z: pd.DataFrame):
    eq = _anchor(Z, EQUITY_CANDIDATES); yld = _anchor(Z, YIELD_CANDIDATES)
    pc1, pc2, ev1, ev2 = [], [], [], []
    load_last = None
    for t in range(1, len(Z)):
        Zi = Z.iloc[:t+1,:]
        if len(Zi)<2: pc1.append(np.nan); pc2.append(np.nan); ev1.append(np.nan); ev2.append(np.nan); continue
        p = PCA(n_components=2).fit(Zi.values)
        scores = p.transform(Zi.values)
        s_t = scores[-1,:].copy(); hist = pd.DataFrame(scores, index=Zi.index, columns=['PC1','PC2'])
        try:
            if hist['PC1'].corr(Zi[eq])<0: hist['PC1']*=-1; s_t[0]*=-1
        except Exception: pass
        try:
            if hist['PC2'].corr(-Zi[yld])<0: hist['PC2']*=-1; s_t[1]*=-1
        except Exception: pass
        pc1.append(s_t[0]); pc2.append(s_t[1]); ev1.append(p.explained_variance_ratio_[0]); ev2.append(p.explained_variance_ratio_[1])
        if t==len(Z)-1:
            comps = p.components_.copy()
            if hist['PC1'].corr(Zi[eq])<0: comps[0,:]*=-1
            if hist['PC2'].corr(-Zi[yld])<0: comps[1,:]*=-1
            load_last = pd.DataFrame(comps.T, index=Z.columns, columns=['PC1','PC2'])
    PC = pd.DataFrame({'PC1':[np.nan]*(len(Z)-len(pc1))+pc1, 'PC2':[np.nan]*(len(Z)-len(pc2))+pc2}, index=Z.index)
    EVR = pd.DataFrame({'PC1_EVR':[np.nan]*(len(Z)-len(ev1))+ev1, 'PC2_EVR':[np.nan]*(len(Z)-len(ev2))+ev2}, index=Z.index)
    EVR['EVR_1_2_sum'] = EVR[['PC1_EVR','PC2_EVR']].sum(axis=1)
    PC['PC1_SMA5'] = PC['PC1'].rolling(5, min_periods=5).mean(); PC['PC2_SMA5'] = PC['PC2'].rolling(5, min_periods=5).mean()
    PC['dPC2'] = PC['PC2'].diff()
    return PC, EVR, (load_last if load_last is not None else pd.DataFrame(index=Z.columns, columns=['PC1','PC2']))

def expanding_loadings_timeline(Z: pd.DataFrame):
    eq = _anchor(Z, EQUITY_CANDIDATES); yld = _anchor(Z, YIELD_CANDIDATES)
    tl = {}
    for t in range(len(Z)):
        Zi = Z.iloc[:t+1,:].dropna(how='any')
        if len(Zi)<2: continue
        p = PCA(n_components=min(2, Zi.shape[1])).fit(Zi.values)
        scores = p.transform(Zi.values)
        hist = pd.DataFrame(scores, index=Zi.index, columns=[f'PC{i+1}' for i in range(p.n_components_)])
        flip1=flip2=1
        try:
            if 'PC1' in hist and hist['PC1'].corr(Zi[eq])<0: hist['PC1']*=-1; flip1=-1
        except Exception: pass
        try:
            if p.n_components_>=2 and hist['PC2'].corr(-Zi[yld])<0: hist['PC2']*=-1; flip2=-1
        except Exception: pass
        comps = p.components_.copy()
        if p.n_components_>=1: comps[0,:]*=flip1
        if p.n_components_>=2: comps[1,:]*=flip2
        L = pd.DataFrame(comps.T, index=Zi.columns, columns=[f'PC{i+1}' for i in range(p.n_components_)])
        L = L.reindex(Z.columns).fillna(0.0)
        tl[Zi.index[-1]] = L
    return tl
