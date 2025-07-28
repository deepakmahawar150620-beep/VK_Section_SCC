import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import kaleido  # ensure kaleido is imported for write_image
from io import BytesIO, StringIO

st.set_page_config(page_title="SCC Risk Explorer", layout="centered")
st.title("📊 SCC Risk Assessment & Graph Explorer")

criteria = {
    "Criterion": [
        "Hoop stress > 60% SMYS",
        "Soil resistivity < 5000 Ω·cm",
        "Distance ≤ 32 km",
        "Pipe age > 10 yrs (≥30 high)",
        "Temp > 38 °C",
        "Coating = CTE or coal‑tar enamel",
        "OFF PSP > −1.2 V"
    ],
    "Description": [
        "High mechanical stress",
        "Corrosive soil",
        "Proximity risk",
        "Older pipe",
        "Thermal acceleration",
        "Vulnerable coating",
        "Over‑protection"
    ]
}
st.subheader("Risk Criteria")
st.table(pd.DataFrame(criteria))

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    df.columns = df.columns.str.strip()
    return df

df0 = load_data()
st.subheader("Data Preview")
st.dataframe(df0.head(50), height=200)

required = [
    "Stationing (m)", "Hoop stress% of SMYS", "Soil Resistivity (Ω-cm)",
    "Distance from Pump(KM)", "Pipe Age", "Temperature",
    "CoatingType", "OFF PSP (VE V)"
]
missing = [c for c in required if c not in df0.columns]
if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

@st.cache_data
def compute_risk(df):
    d = df[required].dropna(subset=["Stationing (m)"]).fillna({
        "Soil Resistivity (Ω-cm)": 1e9,
        "Hoop stress% of SMYS": 0,
        "Pipe Age": 0,
        "Temperature": 0,
        "Distance from Pump(KM)": 1e6,
        "CoatingType": "",
        "OFF PSP (VE V)": -99.0
    }).copy()

    for col in required:
        if col != "CoatingType":
            d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)

    def flags(r):
        return {
            "Stress>60%": r["Hoop stress% of SMYS"] > 60,
            "Soil<5000": r["Soil Resistivity (Ω-cm)"] < 5000,
            "Dist≤32": r["Distance from Pump(KM)"] <= 32,
            "Age≥10": r["Pipe Age"] >= 10,
            "Temp>38": r["Temperature"] > 38,
            "CoatingHigh": any(x in str(r["CoatingType"]).upper() for x in ["CTE", "COAL TAR"]),
            "OFF‑PSP>‑1.2": r["OFF PSP (VE V)"] > -1.2
        }

    flag_df = d.apply(lambda r: pd.Series(flags(r)), axis=1)
    dfc = pd.concat([d, flag_df], axis=1)
    dfc["Risk Score"] = flag_df.sum(axis=1)
    dfc["SCC Risk"] = dfc["Risk Score"].apply(lambda s: "High" if s >= 4 else ("Medium" if s >= 2 else "Low"))
    return dfc

df = compute_risk(df0)
st.subheader("Risk Table Sample")
st.dataframe(df.head(50), height=200)

st.subheader("Interactive Filtering")
df_filt = st.data_editor(df, num_rows="fixed", use_container_width=True)
st.dataframe(df_filt, height=300)

top50 = df.sort_values("Risk Score", ascending=False).head(50)

st.subheader("Plot Explorer")
param = st.selectbox("Select parameter:", [
    "OFF PSP (VE V)", "Hoop stress% of SMYS", "Soil Resistivity (Ω-cm)",
    "Distance from Pump(KM)", "Temperature", "Pipe Age"
])

try:
    fig = go.Figure(go.Scatter(
        x=df["Stationing (m)"], y=df[param],
        mode="lines+markers", line=dict(width=2), marker=dict(size=5)
    ))
except ValueError:
    fig = go.Figure(go.Scatter(
        x=df["Stationing (m)"].tolist(), y=df[param].tolist(),
        mode="lines+markers", line=dict(width=2), marker=dict(size=5)
    ))

if param == "Hoop stress% of SMYS":
    fig.add_hline(y=60, line_color="red", line_dash="dash", annotation_text="60% SMYS")
elif param == "OFF PSP (VE V)":
    fig.add_hline(y=-1.2, line_color="red", line_dash="dash", annotation_text="-1.2 V")

fig.update_layout(
    title=f"Stationing vs {param}",
    xaxis_title="Stationing (m)", yaxis_title=param,
    template="plotly_white", height=420
)
st.plotly_chart(fig, use_container_width=True)

htmlbuf = StringIO()
pio.write_html(fig, htmlbuf, include_plotlyjs="cdn")
st.download_button("⬇️ Download Plot as HTML", htmlbuf.getvalue(),
                   file_name=f"{param.replace(' ', '_')}_plot.html", mime="text/html")

def to_excel(dfs, sheets):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for dfx, name in zip(dfs, sheets):
            dfx.to_excel(writer, sheet_name=name, index=False)
    buf.seek(0)
    return buf.getvalue()

bytes_all = to_excel([df], ["All_Rows"])
bytes_top50 = to_excel([top50], ["Top50_HighRisk"])

st.download_button("⬇️ Download Full Results (Excel)", data=bytes_all,
                   file_name="scc_all_results.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("⬇️ Download Top 50 High‑Risk (Excel)", data=bytes_top50,
                   file_name="scc_top50_highrisk.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
