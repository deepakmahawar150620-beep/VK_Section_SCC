import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import io
from utils import load_data, categorize_risk, get_top_50_risks, generate_pdf_report

# Streamlit app setup
st.set_page_config(page_title="SCC Graph Explorer", layout="centered")
st.title("📈 SCC Risk Graph Explorer")

# Load data using utility function
df = load_data()

# Risk score + filtering
df = categorize_risk(df)
top50_df = get_top_50_risks(df)

# Column label mappings
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

# Select parameter
selected_col = st.selectbox("Select a parameter to compare with Stationing:", list(plot_columns.keys()))
label = plot_columns[selected_col]

# Plot the graph
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['Stationing (m)'],
    y=df[selected_col],
    mode='lines+markers',
    name=label,
    line=dict(width=2),
    marker=dict(size=6)
))

# Threshold lines
if label == 'Hoop Stress (% of SMYS)':
    fig.add_shape(type='line', x0=df['Stationing (m)'].min(), x1=df['Stationing (m)'].max(),
                  y0=60, y1=60, line=dict(color='red', dash='dash'))

elif label == 'OFF PSP (-ve Volt)':
    for yval in [0.85, 1.2]:
        fig.add_shape(type='line', x0=df['Stationing (m)'].min(), x1=df['Stationing (m)'].max(),
                      y0=yval, y1=yval, line=dict(color='red', dash='dash'))

# Layout
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

# Display chart
st.plotly_chart(fig, use_container_width=True)

# Download chart as HTML
html_buffer = io.StringIO()
pio.write_html(fig, file=html_buffer, include_plotlyjs='cdn')
st.download_button(
    label="⬇️ Download High-Quality Graph as HTML",
    data=html_buffer.getvalue(),
    file_name=f"{label.replace(' ', '_')}_graph.html",
    mime="text/html"
)

# Download filtered Top-50 risk PDF
if st.button("📄 Download PDF Report of Top 50 High-Risk Locations"):
    pdf_bytes = generate_pdf_report(top50_df)
    st.download_button(
        label="⬇️ Download SCC Risk Report (PDF)",
        data=pdf_bytes,
        file_name="SCC_High_Risk_Report.pdf",
        mime="application/pdf"
    )
