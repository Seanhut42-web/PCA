import numpy as np, matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from .regimes import shade_regime_bands

def plot_pc_with_sma(ax, series, sma, regime=None, title=''):
    if regime is not None: shade_regime_bands(ax, regime, alpha=0.28)
    y=series.values; ax.bar(series.index, y, width=20, color=np.where(y>=0,'tab:green','tab:red'), alpha=0.75, edgecolor='none', label='Monthly PC')
    ax.plot(sma.index, sma.values, color='k', lw=2, label='SMA(5)'); ax.axhline(0,color='k',lw=1,alpha=0.6)
    ax.set_title(title); ax.legend(loc='upper left')
