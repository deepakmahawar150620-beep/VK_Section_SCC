import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from io import StringIO, BytesIO

st.set_page_config(page_title="SCC Risk Ranking Explorer", layout="centered")
st.title("📊 SCC Risk Ranking & Top‑50 High‑Risk Locations")

# Display static risk criteria
criteria = {
    "Criterion": [
        "Hoop stress > 60% SMYS",
        "Soil resistivity < 5000 Ω·cm",
        "Distance ≤ 32 km",
        "Pipe age > 10 yrs",
        "Temperature > 38 °C",
        "Coating = CTE / coal‑tar enamel",
        "OFF PSP > −1.2 V"
    ],
    "Weight": ["1"] * 7,
    "Description": [
        "High hoop stress",
        "Corrosive soil",
        "Close to pump risk",
        "Aged pipeline",
        "Heat accelerates SCC",
        "Sensitive coating types",
        "Over-protection risk"
    ]
}
st.subheader("📋 Risk Criteria & Scoring")
st.table(pd.DataFrame(criteria))

# Load dataset from GitHub (cached)
@st.cache_data(show_spinner=True)
def load_data():
    url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
    df0 = pd.read_excel(url, engine="openpyxl")
    df0.columns = df0.columns.str.strip()
    return df0

df = load_data()

# Clean and convert key columns
df['Hoop stress% of SMYS'] = (
    pd.to_numeric(df['Hoop stress% of SMYS'].astype(str).str.replace('%','',regex=False), errors='coerce')
    .fillna(0)
)
if df['Hoop stress% of SMYS'].max() < 10:
    df['Hoop stress% of SMYS'] *= 100

df['OFF PSP (VE V)'] = pd.to_numeric(df['OFF PSP (VE V)'], errors='coerce').abs().fillna(0)
df['Distance from Pump(KM)'] = pd.to_numeric(df['Distance from Pump(KM)'], errors='coerce').fillna(1e9)
df['Pipe Age'] = pd.to_numeric(df['Pipe Age'], errors='coerce').fillna(0)
df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce').fillna(0)

# Compute risk flags & score
def flags_row(r):
    return {
        'Stress>60': r['Hoop stress% of SMYS'] > 60,
        'Soil<5000': r['Soil Resistivity (Ω-cm)'] < 5000,
        'Dist≤32': r['Distance from Pump(KM)'] <= 32,
        'Age>10': r['Pipe Age'] > 10,
        'Temp>38': r['Temperature'] > 38,
        'CoatingHigh': any(x in str(r['CoatingType']).upper() for x in ['CTE','COAL TAR']),
        'OFFPSP>−1.2': r['OFF PSP (VE V)'] > -1.2
    }

flag_df = df.apply(flags_row, axis=1)
# fix `.astype(int)` by converting per Series safely
flag_df = flag_df.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

df = pd.concat([df, flag_df], axis=1)
df['Risk Score'] = flag_df.sum(axis=1)
df['SCC Risk'] = df['Risk Score'].apply(lambda x: 'High' if x >= 4 else ('Medium' if x >= 2 else 'Low'))

# Multi-criteria sort for Top 50
top50 = df.sort_values(
    by=['Risk Score', 'Hoop stress% of SMYS', 'OFF PSP (VE V)', 'Distance from Pump(KM)', 'Pipe Age', 'Temperature'],
    ascending=[False, False, False, True, False, False]
).head(50)

st.subheader("🔥 Top 50 High‑Risk Locations")
st.dataframe(top50[[
    'Stationing (m)', 'Risk Score', 'SCC Risk',
    'Hoop stress% of SMYS', 'OFF PSP (VE V)',
    'Distance from Pump(KM)', 'Pipe Age', 'Temperature'
]], height=300)

# Plot explorer
st.subheader("📈 Plot Stationing vs Parameter")
param = st.selectbox("Choose parameter:", [
    'Hoop stress% of SMYS', 'OFF PSP (VE V)',
    'Distance from Pump(KM)', 'Temperature'
])
label_map = {
    'Hoop stress% of SMYS': 'Hoop Stress (% SMYS)',
    'OFF PSP (VE V)': 'OFF PSP (V)',
    'Distance from Pump(KM)': 'Distance from Pump (KM)',
    'Temperature': 'Temperature (°C)'
}
label = label_map[param]

# Build Plotly Figure with fallback
try:
    fig = go.Figure(go.Scatter(
        x=df['Stationing (m)'], y=df[param],
        mode='lines+markers', name=label, line=dict(width=2), marker=dict(size=6)
    ))
except ValueError:
    fig = go.Figure(go.Scatter(
        x=df['Stationing (m)'].tolist(), y=df[param].tolist(),
        mode='lines+markers', name=label, line=dict(width=2), marker=dict(size=6)
    ))

if param == 'Hoop stress% of SMYS':
    fig.add_hline(y=60, line_color='red', line_dash='dash', annotation_text="60% SMYS")
elif param == 'OFF PSP (VE V)':
    fig.add_hline(y=-1.2, line_color='red', line_dash='dash', annotation_text="-1.2 V")

fig.update_layout(
    title=f"Stationing vs {label}",
    xaxis_title='Stationing (m)', yaxis_title=label,
    template='plotly_white', height=450,
    xaxis=dict(showline=True, linecolor='black', mirror=True),
    yaxis=dict(showline=True, linecolor='black', mirror=True, gridcolor='lightgray')
)
st.plotly_chart(fig, use_container_width=True)

# Export Graph HTML
htmlbuf = StringIO()
pio.write_html(fig, htmlbuf, include_plotlyjs='cdn')
st.download_button("⬇️ Download Graph HTML", data=htmlbuf.getvalue(),
                   file_name=f"{label.replace(' ','_')}_plot.html",
                   mime="text/html")

# Export Excel files
def to_excel(dfs, names):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for d, name in zip(dfs, names):
            d.to_excel(writer, sheet_name=name, index=False)
    buf.seek(0)
    return buf.getvalue()

st.download_button("Download Full Risk Table", data=to_excel([df], ['All_Risk']),
                   file_name='scc_full_risk.xlsx',
                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
st.download_button("Download Top 50 High‑Risk", data=to_excel([top50], ['Top50']),
                   file_name='scc_top50.xlsx',
                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
