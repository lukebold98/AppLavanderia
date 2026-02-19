
import os
import sys
from pathlib import Path
import pandas as pd

# Aggiungi la root del progetto al path per gli import
sys.path.append(str(Path(__file__).parent))

from Modules.EYES.unified_reader import UnifiedFileReader

def analyze_pdf_structure():
    pdf_path = "Temp/border_expe_vt.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File {pdf_path} non trovato!")
        return

    print(f"🔍 Analisi approfondita PDF: {pdf_path}")
    
    try:
        reader = UnifiedFileReader()
        # Estraiamo la tabella senza normalizzazione per vedere i nomi colonne originali
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                print("\nColone originali trovate:")
                print(df.columns.tolist())
                
                print("\nPrime 50 righe (grezze):")
                # Mostriamo solo alcune colonne rilevanti se possibile per non intasare
                print(df.head(50).to_string())
                
                # Salviamo su file per analisi dettagliata
                df.head(100).to_csv("dump_pdf_rows.csv", index=False)
                print("\n✅ Dump prime 100 righe salvato in dump_pdf_rows.csv")
            else:
                print("❌ Nessuna tabella trovata nel PDF.")
            
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {e}")

if __name__ == "__main__":
    analyze_pdf_structure()
