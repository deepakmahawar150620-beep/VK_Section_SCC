import streamlit as st
import pandas as pd

st.set_page_config(page_title="GitHub Excel Preview", layout="centered")
st.title("✅ Load Excel from GitHub & Preview All Columns")

@st.cache_data(show_spinner=False)
def load_from_github():
    url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    df.columns = df.columns.str.strip()
    return df

df = load_from_github()
st.write("Detected columns:")
st.write(df.columns.tolist())

st.write("Sample rows (first 5):")
st.dataframe(df.head(5), use_container_width=True)

if 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
    st.success("✅ GPS columns found!")
else:
    st.error("⚠️ GPS columns LATITUDE and/or LONGITUDE are missing.")
