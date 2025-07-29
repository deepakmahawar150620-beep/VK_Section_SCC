import streamlit as st
import pandas as pd

@st.cache_data(show_spinner=False)
def load_default_data():
    url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/VK_Section_SCC/main/Pipeline_VK_Data.xlsx"
    df = pd.read_excel(url, engine="openpyxl", header=0)
    df.columns = df.columns.str.strip()
    return df

# force re-load fresh data every run
load_default_data.clear()
df = load_default_data()

st.write("✅ Columns detected:")
st.write(df.columns.tolist())

st.subheader("📋 Preview first few rows:")
st.dataframe(df.head(5), use_container_width=True)
