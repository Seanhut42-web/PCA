import streamlit as st
import matplotlib.pyplot as plt
from src.plots import plot_pc_with_sma
from src import regimes as regimes_mod

st.title('PC Time Series')

PC = st.session_state.get('PC'); regime = st.session_state.get('regime')
if PC is None or regime is None:
    st.warning('Please upload data and run PCA first.'); st.stop()

fig, ax = plt.subplots(figsize=(14,4.5))
plot_pc_with_sma(ax, PC['PC1'], PC['PC1_SMA5'], title='PC1: Monthly Bars with 5M SMA', regime=regime)

st.pyplot(fig)

fig, ax = plt.subplots(figsize=(14,4.5))
plot_pc_with_sma(ax, PC['PC2'], PC['PC2_SMA5'], title='PC2: Monthly Bars with 5M SMA', regime=regime)

st.pyplot(fig)
