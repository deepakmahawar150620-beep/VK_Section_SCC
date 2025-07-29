import pandas as pd

url = "https://github.com/deepakmahawar150620-beep/VK_Section_SCC/raw/refs/heads/main/Pipeline_VK_Data.xlsx"
df = pd.read_excel(url, engine="openpyxl")
print("Columns loaded:", df.columns.tolist())
print("First row sample:", df.iloc[0].tolist())
