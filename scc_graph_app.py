import pandas as pd

url = "https://raw.githubusercontent.com/deepakmahawar150620-beep/SCC_Pawan/main/Pipeline_data.xlsx"

# Force pandas to read across full column range A:Z (adjust if needed)
df = pd.read_excel(url, engine="openpyxl", header=0, usecols="A:Z")

# Clean up column names
df.columns = df.columns.astype(str).str.strip()

print("Number of columns read:", len(df.columns))
print("Column names:", df.columns.tolist())
print("First row values:", df.iloc[0].tolist())
