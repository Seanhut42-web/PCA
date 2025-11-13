import streamlit as st
import matplotlib.pyplot as plt
from src import regimes as regimes_mod
from src.backtest import hy_ig_strategy

st.title('HY-IG & Risk Bands')

returns = st.session_state.get('returns'); regime = st.session_state.get('regime')
if returns is None or regime is None:
    st.warning('Please upload data and run PCA first.'); st.stop()

res = hy_ig_strategy(returns, regime)

fig, ax = plt.subplots(figsize=(14,6))
regimes_mod.shade_regime_bands(ax, regime)
ax.plot(res['cum_strat'].index, res['cum_strat'], label='PCA Switch (HY/IG)', color='k', lw=2.3)
ax.plot(res['cum_bench'].index, res['cum_bench'], label='EMBI GD', color='tab:blue', lw=2)
ax.set_title('Cumulative Total Return (Start=1) — Regime shading'); ax.set_ylabel('Growth of $1'); ax.legend()

st.pyplot(fig)
