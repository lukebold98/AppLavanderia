
import os
import sys
from pathlib import Path
import pandas as pd

# Aggiungi la root del progetto al path per gli import
sys.path.append(str(Path(__file__).parent))

from Modules.EYES.unified_reader import UnifiedFileReader

def test_pdf():
    pdf_path = "Temp/border_expe_vt.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File {pdf_path} non trovato!")
        return

    print(f"🔍 Test lettura PDF: {pdf_path}")
    
    try:
        reader = UnifiedFileReader()
        df = reader.read_file(pdf_path)
        
        if df is not None and not df.empty:
            print(f"✅ PDF letto con successo! ({len(df)} righe trovate)")
            print(f"Colone trovate: {list(df.columns)}")
            print("\nPrime righe estratte:")
            print(df.head())
        else:
            print("⚠️ Il file è stato letto ma il DataFrame è vuoto o None.")
            
    except Exception as e:
        print(f"❌ Errore durante la lettura del PDF: {e}")

if __name__ == "__main__":
    test_pdf()
