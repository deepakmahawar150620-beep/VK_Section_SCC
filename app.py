import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO, StringIO

# Page Layout
st.set_page_config(page_title="SCC Risk Analyzer", layout="centered")
st.title("📊 SCC Risk Assessment & Graph Explorer")

# Criteria Table
criteria = {
    "Criterion": [
        "Hoop stress > 60% SMYS",
        "Soil resistivity < 5000 Ω·cm",
        "Distance from pump ≤ 32 km",
        "Pipe age > 10 years (≥30 high)",
        "Temperature > 38 °C",
        "Coating = CTE or coal‑tar enamel",
        "OFF PSP > −1.2 V"
    ],
    "Description": [
        "Stress threshold for SCC",
        "Corrosive soil promotes SCC",
        "Close proximity to pump risk",
        "Older pipelines more vulnerable",
        "High temperatures accelerate SCC",
        "Shielding coatings linked to SCC",
        "Over‑protection accelerates cracking"
    ]
}
st.subheader("🧪 Assessment Criteria")
st.table(pd.DataFrame(criteria))

# 🚀 Load and cache the Excel dataset from GitHub
@st.cache_data(show_spinner=True)
def load_pipeline_data():
    url = (
        "https://raw.githubusercontent.com/"
        "deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
    )
    dfg = pd.read_excel(url, engine="openpyxl")
    dfg.columns = dfg.columns.str.strip()
    return dfg

df0 = load_pipeline_data()
st.subheader("Data Preview")
st.dataframe(df0.head(50), height=220)

# Required columns validation
required = [
    "Stationing (m)", "Hoop stress% of SMYS", "Soil Resistivity (Ω-cm)",
    "Distance from Pump(KM)", "Pipe Age", "Temperature",
    "CoatingType", "OFF PSP (VE V)"
]
missing = [c for c in required if c not in df0.columns]
if missing:
    st.error(f"Missing columns in dataset: {missing}")
    st.stop()

# ⚡ Compute risk flags only once, cached
@st.cache_data
def compute_risks(df):
    d = df[required].dropna(subset=["Stationing (m)"]).fillna({
        "Soil Resistivity (Ω-cm)": 1e9,
        "Hoop stress% of SMYS": 0,
        "Pipe Age": 0,
        "Temperature": 0,
        "Distance from Pump(KM)": 1e6,
        "CoatingType": "",
        "OFF PSP (VE V)": -99.0
    }).copy()

    for col in ["Stationing (m)", "Hoop stress% of SMYS", "Soil Resistivity (Ω-cm)",
                "Distance from Pump(KM)", "Pipe Age", "Temperature", "OFF PSP (VE V)"]:
        d[col] = d[col].astype(float)

    def flags(r):
        return {
            "Stress>60%": r["Hoop stress% of SMYS"] > 60,
            "Soil<5000": r["Soil Resistivity (Ω-cm)"] < 5000,
            "Dist≤32": r["Distance from Pump(KM)"] <= 32,
            "Age≥10": r["Pipe Age"] >= 10,
            "Temp>38": r["Temperature"] > 38,
            "CoatingHigh": any(x in str(r["CoatingType"]).upper() for x in ["CTE", "COAL TAR"]),
            "OFF-PSP>−1.2": r["OFF PSP (VE V)"] > -1.2
        }

    flags_df = d.apply(lambda row: pd.Series(flags(row)), axis=1)
    dfc = pd.concat([d, flags_df], axis=1)
    dfc["Risk Score"] = flags_df.sum(axis=1)
    dfc["SCC Risk"] = dfc["Risk Score"].apply(
        lambda s: "High" if s >= 4 else ("Medium" if s >= 2 else "Low")
    )
    return dfc

df = compute_risks(df0)
st.subheader("Risk Table Sample")
st.dataframe(df.head(50), height=220)

# Interactive filter/editor
st.subheader("🔍 Interactive Filtering (fast)")
df_filt = st.data_editor(df, num_rows="fixed", use_container_width=True)
st.dataframe(df_filt, height=300)

# Top 50 high-risk
top50 = df.sort_values("Risk Score", ascending=False).head(50)

# Plot Explorer
st.subheader("📈 Parameter Plot Explorer")
param_choices = [
    "OFF PSP (VE V)", "Hoop stress% of SMYS", "Soil Resistivity (Ω-cm)",
    "Distance from Pump(KM)", "Temperature", "Pipe Age"
]
param = st.selectbox("Select parameter to plot:", param_choices)

fig = go.Figure(go.Scatter(
    x=df["Stationing (m)"], y=df[param],
    mode="lines+markers", stripmode=False,
    name=param, line=dict(width=2), marker=dict(size=5)
))
if param == "Hoop stress% of SMYS":
    fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="60% SMYS")
elif param == "OFF PSP (VE V)":
    fig.add_hline(y=-1.2, line_dash="dash", line_color="red", annotation_text="-1.2 V")

fig.update_layout(
    title=f"Stationing vs {param}",
    xaxis_title="Stationing (m)", yaxis_title=param,
    template="plotly_white", height=420
)
st.plotly_chart(fig, use_container_width=True)

# Graph download
htmlbuf = StringIO()
pio.write_html(fig, htmlbuf, include_plotlyjs="cdn")
st.download_button(
    label="Download Plot as HTML",
    data=htmlbuf.getvalue(),
    file_name=f"{param.replace(' ', '_')}_plot.html",
    mime="text/html"
)

# Excel exports
def to_excel(dataframes, sheet_names):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        for dfx, name in zip(dataframes, sheet_names):
            dfx.to_excel(writer, sheet_name=name, index=False)
    return bio.getvalue()

bytes_all = to_excel([df], ["All_Rows"])
bytes_top50 = to_excel([top50], ["Top_50"])

st.download_button(
    "⬇️ Download Full Results (Excel)",
    data=bytes_all,
    file_name="scc_all_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.download_button(
    "⬇️ Download Top 50 High‑Risk (Excel)",
    data=bytes_top50,
    file_name="scc_top50_highrisk.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
