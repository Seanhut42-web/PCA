import streamlit as st
from src.utils import file_hash
from src import data_ingest

st.title('Upload & Validate')

uploaded = st.file_uploader('Upload your monthly Excel workbook (.xlsx)', type=['xlsx'])
minp = st.number_input('Min periods for expanding z-score (when Inputs used)', min_value=6, max_value=120, value=24)

@st.cache_data(show_spinner=False)
def _cache_parse(xls_bytes: bytes, minp_z:int):
    xf = data_ingest.read_excel_bytes(xls_bytes)
    sheets = data_ingest.detect_sheets(xf)
    Z = data_ingest.load_variables(xf, prefer_raw=True, minp_z=minp_z)
    try:
        returns = data_ingest.load_returns(xf)
    except Exception:
        returns = None
    return sheets, Z, returns

if uploaded is not None:
    key = file_hash(uploaded)
    sheets, Z, returns = _cache_parse(uploaded.getvalue(), minp)
    st.subheader('Detected sheets'); st.json(sheets)
    st.subheader('Z-scores (preview)'); st.dataframe(Z.tail(10))
    if returns is not None:
        st.subheader('Returns (preview)'); st.dataframe(returns.tail(10))
    st.session_state['xls_hash'] = key
    st.session_state['Z'] = Z
    st.session_state['returns'] = returns
    st.success('Workbook parsed and cached. Navigate to the next pages.')
else:
    st.info('Upload a workbook to proceed.')
