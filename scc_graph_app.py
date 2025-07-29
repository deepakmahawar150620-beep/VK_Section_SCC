import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
import plotly.io as pio
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="📊 SCC Risk Graph Explorer", layout="centered")
st.title("📈 SCC Risk Graph Explorer")

@st.cache_data(show_spinner=False)
def load_data():
    url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/VK_Section_SCC/main/Pipeline_VK_Data.xlsx"
    df = pd.read_excel(url, engine="openpyxl", header=0)
    df.columns = df.columns.str.strip()
    return df

# Ensure fresh load on each run
load_data.clear()
df = load_data()

st.subheader("✅ Loaded Excel Data Preview")
st.write("Columns:", df.columns.tolist())
st.dataframe(df.head(5), use_container_width=True)

# Include cleaning and risk logic as before...
# Ensure 'LATITUDE' and 'LONGITUDE' exist before mapping

# ... remaining graph, risk tables, map toggle, etc.
