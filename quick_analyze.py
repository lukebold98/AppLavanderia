
import pdfplumber
import pandas as pd
from pathlib import Path

def quick_analyze():
    pdf_path = "Temp/border_expe_vt.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        table = page.extract_table()
        if table:
            df = pd.DataFrame(table[1:], columns=table[0])
            print("COLUMNS:", df.columns.tolist())
            print("\nDATA (First 20 rows):")
            print(df.head(20).to_string())
        else:
            print("No table found")

if __name__ == "__main__":
    quick_analyze()
