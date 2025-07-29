import pandas as pd

url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/VK_Section_SCC/main/Pipeline_VK_Data.xlsx
"
df = pd.read_excel(url, engine="openpyxl")
print("Columns loaded:", df.columns.tolist())
print("First row sample:", df.iloc[0].tolist())
