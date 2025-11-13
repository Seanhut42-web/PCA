import streamlit as st

st.set_page_config(page_title='PCA Regime App', page_icon='📈', layout='wide')

st.title('PCA Regime Model • HY/IG Switch & Regime Analytics')

st.markdown("""
**Workflow**

1) Go to **Upload & Validate** to upload the monthly Excel workbook.

2) Explore **PCA & Regimes**, **Performance**, **Risk**, **HY−IG**, **PC Time Series**, and **Contributors**.

3) Create a **PDF report** and **Excel/CSV exports**.
""")

st.success('Use the left sidebar pages to get started →')
