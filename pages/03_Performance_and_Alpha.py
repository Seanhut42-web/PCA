import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from src.metrics import rolling_excess, cumulative_excess
from src.backtest import hy_ig_strategy

st.title('Performance & Alpha')

returns = st.session_state.get('returns'); regime = st.session_state.get('regime')
if returns is None or regime is None:
    st.warning('Please upload data and run PCA first.'); st.stop()

res = hy_ig_strategy(returns, regime)
strat = res['strat_ret']; bench = res['bench_ret']

roll = rolling_excess(strat, bench, window=12)
cumx = cumulative_excess(strat, bench)

fig, ax = plt.subplots(figsize=(14,5.5))
ax.plot(roll.index, roll, color='tab:green', lw=2.0, label='12m Rolling Excess (geometric)')
ax.axhline(0, color='k', lw=1); ax.set_title('12-month Rolling Excess Return — Strategy vs EMBI GD'); ax.set_ylabel('Excess return'); ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_: f'{y:.1%}'))
ax.legend(loc='best')

st.pyplot(fig)

fig, ax = plt.subplots(figsize=(14,5.5))
ax.plot(cumx.index, cumx, color='tab:purple', lw=2.2, label='Cumulative Excess (geometric)')
ax.axhline(0, color='k', lw=1); ax.set_title('Cumulative Excess Return — Strategy vs EMBI GD (from start)'); ax.set_ylabel('Cumulative excess'); ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_: f'{y:.1%}'))
ax.legend(loc='best')

st.pyplot(fig)
