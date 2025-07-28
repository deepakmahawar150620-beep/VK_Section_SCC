import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO

# Page config
st.set_page_config(page_title="SCC Risk Explorer", layout="centered")

# Risk criteria display
st.title("📊 SCC Risk Assessment & Graph Explorer")
criteria = {
    "Criterion": [
        "Hoop stress > 60% SMYS",
        "Soil resistivity < 5000 Ω·cm",
        "Distance from pump ≤ 32 km",
        "Pipe age > 10 years (≥30 = high)",
        "Temperature > 38 °C",
        "Coating = CTE or coal‑tar enamel",
        "OFF PSP > −1.2 V"
    ],
    "Description": [
        "High mechanical stress",
        "Corrosive soil environment",
        "Proximity risk",
        "Age increases susceptibility",
        "Thermal acceleration",
        "Sensitive coatings",
        "Over-protection risk"
    ]
}
st.subheader("Assessment Criteria")
st.table(pd.DataFrame(criteria))

# 🧱 Cached loader for Excel file
@st.cache_data(show_spinner=True)
def load_df(uploaded_file):
    df0 = pd.read_excel(uploaded_file, engine="openpyxl")
    df0.columns = [c.strip() for c in df0.columns]
    return df0

uploaded = st.file_uploader("Upload Excel (.xlsx)", type="xlsx")
if not uploaded:
    st.info("Please upload your pipeline data file.")
    st.stop()

df0 = load_df(uploaded)
st.subheader("Uploaded Preview")
st.dataframe(df0.head(), height=200)

# Validate required columns
required = ["Stationing (m)", "Hoop stress% of SMYS", "Soil Resistivity (Ω-cm)",
            "Distance from Pump(KM)", "Pipe Age", "Temperature", "CoatingType", "OFF PSP (VE V)"]
missing = [c for c in required if c not in df0.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# Cached risk computation
@st.cache_data
def compute_risk_table(df):
    df = df[required].dropna(subset=["Stationing (m)"]).fillna({
        "Soil Resistivity (Ω-cm)": 1e9,
        "Hoop stress% of SMYS": 0,
        "Pipe Age": 0,
        "Temperature": 0,
        "Distance from Pump(KM)": 1e6,
        "CoatingType": "",
        "OFF PSP (VE V)": -99.0
    }).copy()
    df = df.astype({
        "Stationing (m)": float,
        "Hoop stress% of SMYS": float,
        "Soil Resistivity (Ω‑cm)": float,
        "Distance from Pump(KM)": float,
        "Pipe Age": float,
        "Temperature": float,
        "OFF PSP (VE V)": float
    })
    def eval_flags(r):
        return pd.Series({
            "Stress>60%": r["Hoop stress% of SMYS"] > 60,
            "Soil<5000": r["Soil Resistivity (Ω-cm)"] < 5000,
            "Dist≤32": r["Distance from Pump(KM)"] <= 32,
            "Age≥10": r["Pipe Age"] >= 10,
            "Temp>38": r["Temperature"] > 38,
            "CoatingHighRisk": any(x in str(r["CoatingType"]).upper() for x in ["CTE", "COAL TAR"]),
            "OFF‑PSP>‑1.2": r["OFF PSP (VE V)"] > -1.2
        })
    flags = df.apply(eval_flags, axis=1)
    df = pd.concat([df, flags], axis=1)
    df["Risk Score"] = flags.sum(axis=1)
    df["SCC Risk"] = df["Risk Score"].apply(lambda x: "High" if x >= 4 else ("Medium" if x >= 2 else "Low"))
    return df

df = compute_risk_table(df0)
st.subheader("Risk Table Sample")
st.dataframe(df.head(50), height=200)

# Filter UI using data_editor (efficient)
st.subheader("Interactive Filtering")
df_filt = st.data_editor(df, num_rows="fixed", use_container_width=True)
st.dataframe(df_filt, height=300)

# Top 50 high‑risk
top50 = df.sort_values("Risk Score", ascending=False).head(50)

# Download full and top50 results as Excel
def to_excel(dfs, sheets):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for d, s in zip(dfs, sheets):
            d.to_excel(writer, sheet_name=s, index=False)
    return buf.getvalue()

excel_full = to_excel([df], ["All_Results"])
excel_top = to_excel([top50], ["Top_50_HighRisk"])

st.download_button("Download Full Results (Excel)", data=excel_full,
                   file_name="scc_full_results.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("Download Top50 High‑Risk (Excel)", data=excel_top,
                   file_name="scc_top50_highrisk.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Plot explorer
st.subheader("Plot Explorer")
plot_choices = ["OFF PSP (VE V)", "Hoop stress% of SMYS", "Soil Resistivity (Ω-cm)",
                "Distance from Pump(KM)", "Temperature", "Pipe Age"]
param = st.selectbox("Choose parameter:", plot_choices)
fig = go.Figure(go.Scatter(x=df["Stationing (m)"], y=df[param],
                           mode='lines+markers', name=param, line=dict(width=2), marker=dict(size=5)))
if param == "Hoop stress% of SMYS":
    fig.add_hline(y=60, line_color="red", line_dash="dash", annotation_text="60% SMYS")
elif param == "OFF PSP (VE V)":
    fig.add_hline(y=-1.2, line_color="red", line_dash="dash", annotation_text="-1.2 V")
fig.update_layout(title=f"Stationing vs {param}", xaxis_title="Stationing (m)", yaxis_title=param,
                  template="plotly_white", height=400)
st.plotly_chart(fig, use_container_width=True)
buf = io.StringIO()
pio.write_html(fig, buf, include_plotlyjs='cdn')
st.download_button("Download Graph as HTML", data=buf.getvalue(),
                   file_name=f"{param}_plot.html", mime="text/html")
