import numpy as np, pandas as pd
from .utils import REGIME_COLORS, RISK_COLORS

def compute_regime(PC: pd.DataFrame) -> pd.Series:
    risk = pd.Series(np.nan, index=PC.index, dtype='object')
    risk[PC['PC1_SMA5']>0] = 'Risk-ON'; risk[PC['PC1_SMA5']<0] = 'Risk-OFF'
    dis = PC['PC2_SMA5']>0
    lab=[]
    for ts in PC.index:
        ro = risk.loc[ts]; s2 = dis.loc[ts] if pd.notna(PC.loc[ts,'PC2_SMA5']) else np.nan
        if pd.isna(ro) or pd.isna(s2): lab.append(np.nan)
        elif ro=='Risk-ON' and s2: lab.append('Goldilocks')
        elif ro=='Risk-ON' and not s2: lab.append('Reflation')
        elif ro=='Risk-OFF' and s2: lab.append('Recession')
        else: lab.append('Stagflation')
    return pd.Series(lab, index=PC.index, name='Regime')

def shade_regime_bands(ax, regime: pd.Series, alpha=0.28):
    reg = regime.dropna();
    if reg.empty: return
    p = reg.index.to_period('M')
    start = p.asfreq('D','start').to_timestamp(); end = (p+1).asfreq('D','start').to_timestamp()
    blocks=(reg!=reg.shift()).cumsum()
    for _, idx in reg.groupby(blocks).groups.items():
        idx=list(idx); lab=reg.loc[idx[0]]
        ax.axvspan(start.loc[idx[0]], end.loc[idx[-1]], color=REGIME_COLORS.get(lab,'#eee'), alpha=alpha, lw=0)
