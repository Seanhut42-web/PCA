import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from src.metrics import calendar_returns, rolling_te_ir
from src.backtest import hy_ig_strategy

st.title('Risk & IR')

returns = st.session_state.get('returns'); regime = st.session_state.get('regime')
if returns is None or regime is None:
    st.warning('Please upload data and run PCA first.'); st.stop()

res = hy_ig_strategy(returns, regime)
strat = res['strat_ret']; bench = res['bench_ret']

cal = calendar_returns(strat, bench)
st.subheader('Calendar-year compounded returns'); st.dataframe((cal*100).round(2))

te_roll, te_over, ir_roll, ir_over, ann_s, ann_b = rolling_te_ir(strat, bench, window=12)

fig, axes = plt.subplots(2,1, figsize=(14,8), sharex=True, gridspec_kw={'height_ratios':[2,1],'hspace':0.1})
axes[0].plot(te_roll.index, te_roll, color='tab:red', lw=2, label='Rolling TE (12m, annualised)')
axes[0].axhline(te_over, color='k', lw=1.2, ls='--', label=f'Overall TE = {te_over:.2%}')
axes[0].set_title('Tracking Error — Rolling vs Overall (annualised)'); axes[0].set_ylabel('TE'); axes[0].yaxis.set_major_formatter(FuncFormatter(lambda y,_: f'{y:.2%}')); axes[0].legend(loc='upper left')
axes[1].plot(ir_roll.index, ir_roll, color='tab:purple', lw=2, label='Rolling IR (12m)')
axes[1].axhline(0, color='k', lw=1); axes[1].set_title('Information Ratio — Rolling (12m)'); axes[1].set_ylabel('IR'); axes[1].legend(loc='upper left')

st.pyplot(fig)

st.info(f"Overall TE: {te_over:.2%} | Strategy ann. return: {ann_s:.2%} | EMBI GD ann. return: {ann_b:.2%} | IR: {ir_over:.2f}")
