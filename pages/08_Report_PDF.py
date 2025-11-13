import streamlit as st
import io
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from src.backtest import hy_ig_strategy
from src import regimes as regimes_mod

st.title('Report (PDF)')

returns = st.session_state.get('returns'); regime = st.session_state.get('regime'); PC = st.session_state.get('PC')
if returns is None or regime is None or PC is None:
    st.warning('Please upload data and run PCA first.'); st.stop()

res = hy_ig_strategy(returns, regime)

buf = io.BytesIO()
with PdfPages(buf) as pdf:
    fig, ax = plt.subplots(figsize=(14,6))
    regimes_mod.shade_regime_bands(ax, regime, alpha=0.28)
    ax.plot(res['cum_strat'].index, res['cum_strat'], label='PCA Switch (HY/IG)', color='k', lw=2.3)
    ax.plot(res['cum_bench'].index, res['cum_bench'], label='EMBI GD', color='tab:blue', lw=2)
    ax.set_title('Cumulative Total Return (Start=1)'); ax.set_ylabel('Growth of $1'); ax.legend(); pdf.savefig(fig); plt.close(fig)

st.download_button('Download Report.pdf', data=buf.getvalue(), file_name='PCA_Regime_Report.pdf', mime='application/pdf')
