import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import io

st.set_page_config(page_title="SCC Risk Assessment", layout="wide")
st.title("📊 SCC Risk Assessment & Graph Explorer")

# Read data
url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
df = pd.read_excel(url, engine="openpyxl")
df.columns = [col.strip() for col in df.columns]

# Preprocess data
df['OFF PSP (VE V)'] = df['OFF PSP (VE V)'].astype(float).abs()

if 'Hoop stress% of SMYS' in df.columns:
    df['Hoop stress% of SMYS'] = df['Hoop stress% of SMYS'].astype(str).str.replace('%', '').astype(float)
    if df['Hoop stress% of SMYS'].max() < 10:
        df['Hoop stress% of SMYS'] *= 100

# Risk Criteria Function
def flags_row(row):
    return {
        'Hoop Stress > 60%': 1 if row['Hoop stress% of SMYS'] > 60 else 0,
        'Soil Resistivity < 5000': 1 if row['Soil Resistivity (Ω-cm)'] < 5000 else 0,
        'Distance from Pump ≤ 32': 1 if row['Distance from Pump(KM)'] <= 32 else 0,
        'Pipe Age > 10': 1 if row['Pipe Age'] > 10 else 0,
        'Pipe Age ≥ 30': 1 if row['Pipe Age'] >= 30 else 0,
        'Temp > 38°C': 1 if row['Temperature'] > 38 else 0,
        'Coating Type Sensitive': 1 if str(row['Coating Type']).strip().lower() in ['cte', 'coal-tar enamel'] else 0,
        'OFF PSP > 1.2V': 1 if row['OFF PSP (VE V)'] > 1.2 else 0
    }

flag_df = df.apply(flags_row, axis=1).apply(pd.to_numeric, errors='coerce')
flag_df = flag_df.fillna(0)
flag_df = flag_df.astype(int)

# Calculate risk score
df['SCC Risk Score'] = flag_df.sum(axis=1)

# Combine back
df_risk = pd.concat([df, flag_df], axis=1)

# Top 50 high-risk locations
top50 = df_risk.sort_values(
    by=['SCC Risk Score', 'Hoop stress% of SMYS', 'OFF PSP (VE V)', 'Distance from Pump(KM)'],
    ascending=[False, False, False, True]
).head(50)

# Show top 50 results
st.subheader("🛑 Top 50 High-Risk Locations")
st.dataframe(top50[['Stationing (m)', 'SCC Risk Score', 'Hoop stress% of SMYS', 'OFF PSP (VE V)', 'Distance from Pump(KM)', 'Pipe Age'] + list(flag_df.columns)])

# Plotting
plot_columns = {
    'Depth (mm)': 'Depth (mm)',
    'OFF PSP (VE V)': 'OFF PSP (-ve Volt)',
    'Soil Resistivity (Ω-cm)': 'Soil Resistivity (Ω-cm)',
    'Distance from Pump(KM)': 'Distance from Pump (KM)',
    'Operating Pr.': 'Operating Pressure',
    'Remaining Thickness(mm)': 'Remaining Thickness (mm)',
    'Hoop stress% of SMYS': 'Hoop Stress (% of SMYS)',
    'Temperature': 'Temperature (°C)',
    'Pipe Age': 'Pipe Age'
}
selected_col = st.selectbox("📌 Select a parameter to compare with Stationing:", list(plot_columns.keys()))
label = plot_columns[selected_col]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['Stationing (m)'],
    y=df[selected_col],
    mode='lines+markers',
    name=label,
    line=dict(width=2),
    marker=dict(size=6)
))

# Thresholds
if label == 'Hoop Stress (% of SMYS)':
    fig.add_shape(type='line', x0=df['Stationing (m)'].min(), x1=df['Stationing (m)'].max(),
                  y0=60, y1=60, line=dict(color='red', dash='dash'))
elif label == 'OFF PSP (-ve Volt)':
    for yval in [0.85, 1.2]:
        fig.add_shape(type='line', x0=df['Stationing (m)'].min(), x1=df['Stationing (m)'].max(),
                      y0=yval, y1=yval, line=dict(color='red', dash='dash'))

fig.update_layout(
    title=f"📍 Stationing vs {label}",
    xaxis_title="Stationing (m)",
    yaxis_title=label,
    height=500,
    template='plotly_white',
    margin=dict(l=60, r=40, t=50, b=60),
    xaxis=dict(showline=True, linecolor='black', mirror=True),
    yaxis=dict(showline=True, linecolor='black', mirror=True, gridcolor='lightgray')
)
st.plotly_chart(fig, use_container_width=True)

# HTML download
html_buffer = io.StringIO()
pio.write_html(fig, file=html_buffer, include_plotlyjs='cdn')
st.download_button(
    label="⬇️ Download Graph as HTML",
    data=html_buffer.getvalue(),
    file_name=f"{label.replace(' ', '_')}_graph.html",
    mime="text/html"
)
