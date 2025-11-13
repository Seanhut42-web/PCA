import streamlit as st
import matplotlib.pyplot as plt
from src import pca as pca_mod
from src import regimes as regimes_mod

st.title('PCA & Regimes')

Z = st.session_state.get('Z')
if Z is None:
    st.warning('Please upload data on the Upload page.'); st.stop()

PC, EVR, loadings = pca_mod.expanding_pca_2(Z)
regime = regimes_mod.compute_regime(PC)

st.session_state['PC'] = PC
st.session_state['EVR'] = EVR
st.session_state['regime'] = regime
st.session_state['loadings_latest'] = loadings

fig, axes = plt.subplots(3,1, figsize=(14,10), sharex=True, gridspec_kw={'height_ratios':[2,2,1], 'hspace':0.1})
regimes_mod.shade_regime_bands(axes[0], regime)
axes[0].plot(PC.index, PC['PC1'], label='PC1', color='tab:blue'); axes[0].plot(PC.index, PC['PC1_SMA5'], label='SMA(5)', color='k', ls='--'); axes[0].legend(); axes[0].set_title('PC1 & SMA(5)')
regimes_mod.shade_regime_bands(axes[1], regime)
axes[1].plot(PC.index, PC['PC2'], label='PC2', color='tab:orange'); axes[1].plot(PC.index, PC['PC2_SMA5'], label='SMA(5)', color='k', ls='--'); axes[1].legend(); axes[1].set_title('PC2 & SMA(5)')
regimes_mod.shade_regime_bands(axes[2], regime); axes[2].bar(PC.index, PC['dPC2'], color=['tab:green' if v>0 else 'tab:red' for v in PC['dPC2'].fillna(0.0)]); axes[2].axhline(0,color='k'); axes[2].set_title('Delta PC2')

st.pyplot(fig)

st.subheader('Latest loadings (sign-adjusted)')
st.dataframe(loadings.sort_index())
