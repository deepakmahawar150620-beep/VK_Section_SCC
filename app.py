import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from io import StringIO

st.set_page_config(page_title="SCC Graph Explorer", layout="centered")
st.title("📈 SCC Risk Graph Explorer")

# Cache loading of Excel from GitHub
@st.cache_data(show_spinner=True)
def load_df():
    url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    df.columns = df.columns.str.strip()
    return df

df = load_df()

# Cleanup OFF PSP (take absolute) and Hoop stress conversion
if 'OFF PSP (VE V)' in df:
    df['OFF PSP (VE V)'] = df['OFF PSP (VE V)'].astype(float).abs()

if 'Hoop stress% of SMYS' in df:
    df['Hoop stress% of SMYS'] = (
        pd.to_numeric(df['Hoop stress% of SMYS'].astype(str).str.replace('%', '', regex=False), errors='coerce')
        .fillna(0)
    )
    if df['Hoop stress% of SMYS'].max() < 10:
        df['Hoop stress% of SMYS'] *= 100

# Map dropdown columns to labels
plot_columns = {
    'Depth (mm)': 'Depth (mm)',
    'OFF PSP (VE V)': 'OFF PSP (V)',
    'Soil Resistivity (Ω-cm)': 'Soil Resistivity (Ω-cm)',
    'Distance from Pump(KM)': 'Distance from Pump (KM)',
    'Operating Pr.': 'Operating Pressure',
    'Remaining Thickness(mm)': 'Remaining Thickness (mm)',
    'Hoop stress% of SMYS': 'Hoop Stress (% SMYS)',
    'Temperature': 'Temperature (°C)',
    'Pipe Age': 'Pipe Age'
}

col = st.selectbox("Select parameter to compare with Stationing:", list(plot_columns.keys()))
label = plot_columns[col]

# Build the plot, with fallback for Plotly bug
try:
    fig = go.Figure(go.Scatter(
        x=df['Stationing (m)'],
        y=df[col],
        mode='lines+markers',
        name=label,
        line=dict(width=2),
        marker=dict(size=6)
    ))
except ValueError:
    fig = go.Figure(go.Scatter(
        x=df['Stationing (m)'].tolist(),
        y=df[col].tolist(),
        mode='lines+markers',
        name=label,
        line=dict(width=2),
        marker=dict(size=6)
    ))

# Add threshold lines if needed
if label == 'Hoop Stress (% SMYS)':
    fig.add_shape(type='line',
                  x0=df['Stationing (m)'].min(),
                  x1=df['Stationing (m)'].max(),
                  y0=60, y1=60,
                  line=dict(color='red', dash='dash'))
elif label == 'OFF PSP (V)':
    for thresh in [0.85, 1.2]:
        fig.add_shape(type='line',
                      x0=df['Stationing (m)'].min(),
                      x1=df['Stationing (m)'].max(),
                      y0=thresh, y1=thresh,
                      line=dict(color='red', dash='dash'))

# Style layout
fig.update_layout(
    title=f"Stationing vs {label}",
    xaxis_title="Stationing (m)",
    yaxis_title=label,
    height=500,
    template='plotly_white',
    xaxis=dict(showline=True, linecolor='black', mirror=True),
    yaxis=dict(showline=True, linecolor='black', mirror=True, gridcolor='lightgray'),
    margin=dict(l=60, r=40, t=50, b=60)
)

st.plotly_chart(fig, use_container_width=True)

# HTML download export
html_buf = StringIO()
pio.write_html(fig, file=html_buf, include_plotlyjs='cdn')
st.download_button(
    label="⬇️ Download High‑Quality Graph as HTML",
    data=html_buf.getvalue(),
    file_name=f"{label.replace(' ', '_')}_graph.html",
    mime="text/html"
)
