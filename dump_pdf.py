
import os
import sys
from pathlib import Path
import pandas as pd

# Aggiungi la root del progetto al path per gli import
sys.path.append(str(Path(__file__).parent))

from Modules.EYES.unified_reader import UnifiedFileReader

def dump_pdf_data():
    pdf_path = "Temp/border_expe_vt.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File {pdf_path} non trovato!")
        return

    try:
        reader = UnifiedFileReader()
        df = reader.read_file(pdf_path)
        
        if df is not None and not df.empty:
            print(f"✅ PDF letto: {len(df)} righe")
            # Salva tutto per analisi locale
            df.to_csv("full_dump.csv", index=False)
            print("✅ Dump completo salvato in full_dump.csv")
            
            # Stampa le prime 100 righe per me
            print("\n--- PRIME 100 RIGHE ---")
            print(df.head(100).to_string())
        else:
            print("⚠️ DataFrame vuoto")
            
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    dump_pdf_data()
