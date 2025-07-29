import pandas as pd

url = "https://raw.githubusercontent.com/<username>/<repo>/<branch>/<path>/<filename>.xlsx
"
df = pd.read_excel(url, engine="openpyxl")
print("Columns loaded:", df.columns.tolist())
print("First row sample:", df.iloc[0].tolist())
