import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src import pca as pca_mod

st.title('Contributors (Current)')

Z = st.session_state.get('Z'); PC = st.session_state.get('PC'); regime = st.session_state.get('regime')
if Z is None or PC is None or regime is None:
    st.warning('Please upload data and run PCA first.'); st.stop()

@st.cache_data(show_spinner=False)
def _timeline(Z):
    return pca_mod.expanding_loadings_timeline(Z)

load_tl = _timeline(Z)
valid = PC[['PC1_SMA5','PC2_SMA5']].notna().all(axis=1) & regime.notna()
if not valid.any():
    st.error('Need at least 5 months to compute SMA(5) and a valid regime.'); st.stop()

t0 = PC.index[valid][-1]; reg_now = str(regime.loc[t0])
pc1_sma = float(PC.loc[t0, 'PC1_SMA5']); pc2_sma = float(PC.loc[t0, 'PC2_SMA5'])

st.info(f"Current regime ({t0.date()}): {reg_now} — PC1_SMA5={pc1_sma:+.3f}, PC2_SMA5={pc2_sma:+.3f}")

win = PC.index[max(0, list(PC.index).index(t0)-4): list(PC.index).index(t0)+1]
C1_list, C2_list = [], []
for dt in win:
    L = load_tl.get(dt)
    if L is None: continue
    z = Z.loc[dt].reindex(L.index).fillna(0.0)
    c1 = z * L.get('PC1', pd.Series(0.0, index=L.index))
    c2 = z * L.get('PC2', pd.Series(0.0, index=L.index))
    C1_list.append(c1); C2_list.append(c2)

if len(C1_list)==0: st.error('No per-date oriented loadings available for the last 5 months.'); st.stop()

C1 = pd.concat(C1_list, axis=1).mean(axis=1)
C2 = pd.concat(C2_list, axis=1).mean(axis=1)

fig, axes = plt.subplots(1,2, figsize=(16,5))
for ax, s, title in [(axes[0], C1.sort_values(ascending=False)[:20], 'PC1 (Risk Appetite) — Top vars'), (axes[1], C2.sort_values(ascending=False)[:20], 'PC2 (Duration Demand) — Top vars')]:
    cols = np.where(s.values>=0, 'tab:green','tab:red'); ax.barh(s.index, s.values, color=cols); ax.axvline(0,color='k',lw=1,alpha=0.7); ax.invert_yaxis(); ax.set_title(title)

st.pyplot(fig)

st.download_button('Download variable_contribs_current.csv', data=C1.to_csv().encode('utf-8'), file_name='variable_contribs_current.csv', mime='text/csv')
st.download_button('Download group_contribs_current.csv', data=pd.DataFrame({'PC1_SMA5': C1, 'PC2_SMA5': C2}).to_csv().encode('utf-8'), file_name='group_contribs_current.csv', mime='text/csv')
