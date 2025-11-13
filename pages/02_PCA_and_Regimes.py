import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src import pca as pca_mod
from src import regimes as regimes_mod

st.title('PCA & Regimes')

# Expect Z (z-scores) in session_state from the Upload page
Z = st.session_state.get('Z')
if Z is None:
    st.warning('Please upload data on the Upload page.'); st.stop()

# Run PCA (your existing expanding PCA)
PC, EVR, loadings = pca_mod.expanding_pca_2(Z)

# Compute regimes using your existing logic
regime_raw = regimes_mod.compute_regime(PC)

# --- Make a clean datetime-indexed Series of regime labels ---
def _as_regime_series(obj) -> pd.Series:
    # If already a Series, ensure datetime index
    if isinstance(obj, pd.Series):
        s = obj.copy()
        if not isinstance(s.index, pd.DatetimeIndex):
            s.index = pd.to_datetime(s.index, errors='coerce')
        return s.dropna()
    # If a DataFrame, prefer ['Date','Regime'] if present
    if isinstance(obj, pd.DataFrame):
        cols = [c.strip() for c in obj.columns.map(str)]
        df = obj.copy()
        df.columns = cols
        if 'Date' in cols and 'Regime' in cols:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date']).set_index('Date')
            return df['Regime']
        # else: if single column, squeeze it
        if df.shape[1] == 1:
            s = df.squeeze()
            if not isinstance(s.index, pd.DatetimeIndex):
                s.index = pd.to_datetime(s.index, errors='coerce')
            return s.dropna()
    # Fallback: attempt to coerce generically
    s = pd.Series(obj)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index, errors='coerce')
    return s.dropna()

regime = _as_regime_series(regime_raw)

# --- Safe regime shading: no `.loc` on DatetimeIndex ---
REGIME_COLORS = {
    "ON": "tab:green",
    "OFF": "tab:red",
    "IG/HY": "tab:purple",
    # fallback color if label unknown
}

def shade_regime_bands(ax, reg: pd.Series, alpha: float = 0.15):
    """
    Shade contiguous regime segments on the given axes.
    reg: Series of labels indexed by datetime.
    """
    if not isinstance(reg.index, pd.DatetimeIndex):
        reg.index = pd.to_datetime(reg.index, errors='coerce')
        reg = reg.dropna()

    # Contiguous blocks where label is constant
    blocks = (reg != reg.shift()).cumsum()
    for _, idx in reg.groupby(blocks).groups.items():
        idx = list(idx)                 # list of Timestamps
        if not idx:
            continue
        label = reg.loc[idx[0]]
        start_ts, end_ts = idx[0], idx[-1]
        ax.axvspan(start_ts, end_ts, color=REGIME_COLORS.get(label, "lightgrey"),
                   alpha=alpha, lw=0)

# Persist to session (as before)
st.session_state['PC'] = PC
st.session_state['EVR'] = EVR
st.session_state['regime'] = regime
st.session_state['loadings_latest'] = loadings

# --- Plot ---
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True,
                         gridspec_kw={'height_ratios':[2,2,1], 'hspace':0.1})

# PC1
shade_regime_bands(axes[0], regime)
axes[0].plot(PC.index, PC['PC1'], label='PC1', color='tab:blue')
if 'PC1_SMA5' in PC.columns:
    axes[0].plot(PC.index, PC['PC1_SMA5'], label='SMA(5)', color='k', ls='--')
axes[0].legend(); axes[0].set_title('PC1 & SMA(5)')

# PC2
shade_regime_bands(axes[1], regime)
axes[1].plot(PC.index, PC['PC2'], label='PC2', color='tab:orange')
if 'PC2_SMA5' in PC.columns:
    axes[1].plot(PC.index, PC['PC2_SMA5'], label='SMA(5)', color='k', ls='--')
axes[1].legend(); axes[1].set_title('PC2 & SMA(5)')

# ΔPC2 bars
shade_regime_bands(axes[2], regime)
if 'dPC2' in PC.columns:
    axes[2].bar(
        PC.index,
        PC['dPC2'].fillna(0.0),
        color=['tab:green' if v > 0 else 'tab:red' for v in PC['dPC2'].fillna(0.0)]
    )
axes[2].axhline(0, color='k')
axes[2].set_title('Delta PC2')

st.pyplot(fig)

st.subheader('Latest loadings (sign-adjusted)')
st.dataframe(loadings.sort_index())