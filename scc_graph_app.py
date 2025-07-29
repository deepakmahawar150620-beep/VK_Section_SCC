import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GPS Loader Test", layout="centered")
st.title("📂 Upload & Preview All Columns (including GPS)")

uploaded = st.file_uploader("Upload an Excel file (.xlsx)", type=["xlsx"])
if uploaded is not None:
    raw = uploaded.getvalue()
    df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    df.columns = df.columns.str.strip()
    
    st.write("✅ Detected Columns:")
    st.write(df.columns.tolist())
    
    st.write("📋 Sample Rows:")
    st.dataframe(df.head(5), use_container_width=True)
else:
    st.info("Please upload your Excel file to preview columns.")
