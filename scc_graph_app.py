import pandas as pd

url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"
df = pd.read_excel(url, engine="openpyxl", header=0)
df.columns = df.columns.astype(str).str.strip()
print("Number of columns read:", len(df.columns))
print("Column names:", df.columns.tolist())
print("Sample header row values:")
print(df.iloc[0].tolist())
