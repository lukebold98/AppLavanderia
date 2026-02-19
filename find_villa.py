
import pdfplumber
import pandas as pd

def find_villa_nancy():
    pdf_path = "Temp/border_expe_vt.pdf"
    found_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
                
            # Cerca "VILLA NANCY" in ogni riga
            for row in table:
                row_str = " ".join([str(cell) for cell in row if cell is not None])
                if "VILLA NANCY" in row_str.upper() or "19" in row_str:
                    found_rows.append(row)
    
    if found_rows:
        print(f"Trovate {len(found_rows)} righe potenzialmente rilevanti:")
        for r in found_rows:
            print(r)
    else:
        print("Non ho trovato VILLA NANCY o l'armadietto 19.")

if __name__ == "__main__":
    find_villa_nancy()
