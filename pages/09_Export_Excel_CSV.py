import streamlit as st
from src.exporters import export_labels_basic, export_labels_strategy

st.title('Export (Excel/CSV)')

returns = st.session_state.get('returns'); regime = st.session_state.get('regime')
if returns is None or regime is None:
    st.warning('Please upload data and run PCA first.'); st.stop()

col1, col2 = st.columns(2)
with col1:
    st.subheader('Basic labels (Date, Regime, Risk_On)')
    b = export_labels_basic(returns, regime)
    st.download_button('Download Regime_RiskOn_Labels.xlsx', data=b, file_name='Regime_RiskOn_Labels.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
with col2:
    st.subheader('Labels + Sleeve + Strategy return (no look-ahead)')
    b = export_labels_strategy(returns, regime)
    st.download_button('Download Regime_RiskOn_Sleeve_Strategy.xlsx', data=b, file_name='Regime_RiskOn_Sleeve_Strategy.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
