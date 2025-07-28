# utils.py

import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
import plotly.io as pio

def load_data():
    """Load and clean the main Pipeline_data.xlsx from GitHub."""
    url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    df.columns = df.columns.str.strip()

    if 'OFF PSP (VE V)' in df.columns:
        df['OFF PSP (VE V)'] = pd.to_numeric(df['OFF PSP (VE V)'], errors='coerce').abs().fillna(0)

    if 'Hoop stress% of SMYS' in df.columns:
        hs = pd.to_numeric(df['Hoop stress% of SMYS'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
        if hs.max() < 10:
            hs *= 100
        df['Hoop stress% of SMYS'] = hs

    df['Distance from Pump(KM)'] = pd.to_numeric(df.get('Distance from Pump(KM)', 0), errors='coerce').fillna(1e6)
    df['Pipe Age'] = pd.to_numeric(df.get('Pipe Age', 0), errors='coerce').fillna(0)
    df['Temperature'] = pd.to_numeric(df.get('Temperature', 0), errors='coerce').fillna(0)
    df['Soil Resistivity (Ω-cm)'] = pd.to_numeric(df.get('Soil Resistivity (Ω-cm)', 0), errors='coerce').fillna(1e9)

    df['CoatingType'] = df.get('CoatingType', '').astype(str)
    return df

def flag_criteria(df):
    """Return DataFrame of binary flags per SCC risk criterion."""
    return pd.DataFrame({
        'Stress>60': (df['Hoop stress% of SMYS'] > 60).astype(int),
        'Age>10yrs': (df['Pipe Age'] > 10).astype(int),
        'Temp>38C': (df['Temperature'] > 38).astype(int),
        'Dist≤32km': (df['Distance from Pump(KM)'] <= 32).astype(int),
        'CoatingHighRisk': (~df['CoatingType'].str.upper().isin(['FBE','LIQUID EPOXY'])).astype(int),
        'Soil<5000': (df['Soil Resistivity (Ω-cm)'] < 5000).astype(int),
        'OFFPSP>−1.2V': (df['OFF PSP (VE V)'] > -1.2).astype(int)
    })

def compute_risk_score(df, flags):
    """Compute normalized risk score from continuous variables."""
    hs = df['Hoop stress% of SMYS'] / 100.0
    psp = 1 - ((df['OFF PSP (VE V)'] + 2) / 2)  # invert PSP scale
    max_dist = df['Distance from Pump(KM)'].replace(0, np.nan).max() or 1
    dist_norm = (max_dist - df['Distance from Pump(KM)']) / max_dist
    soil_norm = 1 - np.clip(df['Soil Resistivity (Ω-cm)'] / 10000, 0, 1)

    weights = {'hs': 0.6, 'psp': 0.3, 'dist': 0.2, 'soil': 0.1}
    return hs * weights['hs'] + psp * weights['psp'] + dist_norm * weights['dist'] + soil_norm * weights['soil']

def get_top_50_risks(df):
    """Return full df with flags, scores, categories, and a Top 50 subset."""
    flags = flag_criteria(df)
    risk_score = compute_risk_score(df, flags)
    df_flags = pd.concat([df, flags], axis=1)
    df_flags['RiskScore'] = risk_score
    df_flags['FlagsSum'] = flags.sum(axis=1)
    df_flags['RiskCategory'] = df_flags['FlagsSum'].apply(lambda x: 'High' if x >= 4 else ('Medium' if x >= 2 else 'Low'))

    top50 = df_flags.sort_values(
        by=['RiskScore', 'Hoop stress% of SMYS', 'OFF PSP (VE V)', 'Distance from Pump(KM)'],
        ascending=[False, False, False, True]
    ).head(50)

    return df_flags, top50

def generate_pdf_report(top50_df, fig, title="SCC Top 50 High‑Risk Report"):
    """
    Generate a PDF bytes report containing the Top 50 table and the Plotly figure.
    Uses plotly.io or write_image via kaleido and simple in-memory buffer.
    """
    # First: get figure as PNG bytes
    img_bytes = fig.to_image(format="png", width=800, height=400)

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image as RLImage
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elems = [Paragraph(title, styles['Title']), Spacer(1, 12)]

    # Add data table
    data = [list(top50_df.columns)]
    data += top50_df.values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('GRID',(0,0),(-1,-1),0.25,colors.black),
        ('FONTSIZE',(0,0),(-1,-1),6),
    ]))
    elems.append(table)
    elems.append(Spacer(1,12))

    # Add plot image
    elems.append(Paragraph("Selected Risk Plot", styles['Heading2']))
    img_buf = io.BytesIO(img_bytes)
    elems.append(RLImage(img_buf, width=600, height=300))
    elems.append(Spacer(1,12))

    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()
