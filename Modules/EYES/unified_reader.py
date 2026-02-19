"""
Unified File Reader - Supporto XLS, PDF, e Immagini

Questo modulo unifica la lettura di file da diverse fonti:
- Excel (.xlsx, .xls) → lettura diretta con pandas
- PDF nativo → estrazione tabelle con pdfplumber
- PDF scannerizzato / Immagini → OCR con Mindee (fallback)

SCOPO:
Rendere l'app resiliente a qualsiasi formato l'ufficio personale possa inviare.

STRATEGIA:
1. Rileva tipo file dall'estensione
2. Prova metodo migliore per quel tipo
3. Fallback su OCR se estrazione tabella fallisce
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, IO, Any
import logging
from io import BytesIO

# PDF support
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("pdfplumber non installato - supporto PDF limitato")

# XLS support
from Modules.EYES.xls_reader import XLSReader, ExcelReaderError

# OCR fallback - DISABILITATO (Codice archiviato su richiesta)
# from Modules.EYES.ocr_engine import MindeeOcrEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedFileReader:
    """
    Reader universale che gestisce Excel, PDF, e immagini.
    
    Features:
    - Auto-detect formato file
    - Estrazione intelligente (tabelle vs OCR)
    - Fallback robusto se metodo preferito fallisce
    
    Esempio:
        reader = UnifiedFileReader()
        df = reader.read_file("bolla.pdf")  # Funziona!
        df = reader.read_file("bolla.xlsx") # Funziona!
    """
    
    # Mapping estensioni → metodi
    EXCEL_EXTENSIONS = {'.xlsx', '.xls'}
    PDF_EXTENSIONS = {'.pdf'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
    
    def __init__(self):
        """Inizializza reader con tutti i backend disponibili."""
        self.xls_reader = XLSReader()
        
        # OCR disabilitato per policy di pulizia
        self.ocr_available = False

    
    
    def read_file(self, file_source: Union[str, Path, IO], filename: Optional[str] = None) -> pd.DataFrame:
        """
        Legge file e ritorna DataFrame standardizzato.
        
        Args:
            file_source: Path al file o oggetto file-like
            filename: Nome del file (necessario se file_source è un buffer per dedurre il tipo)
        """
        
        # Determina estensione
        if isinstance(file_source, (str, Path)):
            path = Path(file_source)
            if not path.exists():
                raise ValueError(f"File non trovato: {file_source}")
            extension = path.suffix.lower()
            name = path.name
        else:
            # È un buffer
            if not filename:
                raise ValueError("filename necessario quando si usa un buffer")
            extension = Path(filename).suffix.lower()
            name = filename
        
        logger.info(f"Lettura file: {name} (tipo: {extension})")
        
        # ===== EXCEL =====
        if extension in self.EXCEL_EXTENSIONS:
            return self._read_excel(file_source)
        
        # ===== PDF =====
        elif extension in self.PDF_EXTENSIONS:
            return self._read_pdf(file_source)
        
        # ===== IMMAGINI =====
        elif extension in self.IMAGE_EXTENSIONS:
            return self._read_image_ocr(file_source)
        
        else:
            raise ValueError(f"Formato '{extension}' non supportato.")
    
    
    def _read_excel(self, source: Any) -> pd.DataFrame:
        """Legge file Excel da path o buffer."""
        try:
            # Passiamo la sorgente così com'è (XLSReader ora gestisce entrambi)
            df = self.xls_reader.read_file(source)
            logger.info("Excel letto con successo")
            return df
        except Exception as e:
            raise ValueError(f"Errore lettura Excel: {e}")
    
    
    def _read_pdf(self, source: Any) -> pd.DataFrame:
        """Legge PDF, prova prima estrazione tabella, poi OCR."""
        
        # STEP 1: Prova estrazione tabella (PDF nativo)
        if PDF_SUPPORT:
            try:
                df = self._extract_pdf_table(source)
                if df is not None and len(df) > 0:
                    return df
                else:
                    logger.warning("Estrazione tabella PDF vuota, provo OCR...")
            except Exception as e:
                logger.warning(f"Estrazione tabella fallita: {e}, provo OCR...")
        
        # STEP 2: Fallback OCR (PDF scannerizzato)
        if self.ocr_available:
            logger.info("Usando OCR Mindee per PDF...")
            return self._read_image_ocr(source)
        else:
            raise ValueError(
                "PDF non leggibile come tabella e OCR non disponibile.\n"
                "Installa pdfplumber o configura Mindee API."
            )
    
    
    def _extract_pdf_table(self, source: Any) -> Optional[pd.DataFrame]:
        """
        Estrae tabella da PDF nativo usando pdfplumber.
        """
        if not PDF_SUPPORT:
            return None
        
        all_tables = []
        
        with pdfplumber.open(source) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                
                # Estrai tabelle da questa pagina
                tables = page.extract_tables()
                
                if not tables:
                    logger.debug(f"Pagina {page_num}: nessuna tabella trovata")
                    continue
                
                for table_idx, table in enumerate(tables):
                    # Converti in DataFrame
                    df = pd.DataFrame(table[1:], columns=table[0])  # Prima riga = header
                    
                    logger.debug(f"Pagina {page_num}, Tabella {table_idx}: {len(df)} righe")
                    all_tables.append(df)
        
        if not all_tables:
            return None
        
        # Unisci tutte le tabelle trovate
        combined = pd.concat(all_tables, ignore_index=True)
        
        # Normalizza nomi colonne (rimuovi spazi, lowercase)
        combined.columns = [str(col).strip().lower() for col in combined.columns]
        
        # Mappa a colonne standard se possibile
        combined = self._normalize_pdf_columns(combined)
        
        return combined
    
    
    def _normalize_pdf_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizza colonne PDF per matchare formato atteso.
        
        Cerca colonne con nomi simili a: arm, nome, codice, descrizione
        """
        
        # Mapping flessibile (key = nome standard, value = possibili varianti)
        column_map = {}
        current_cols = df.columns.tolist()
        
        mappings = {
            'arm': ['arm', 'armadietto', 'armadio', 'locker', 'n.arm', 'n. arm'],
            'nome': ['nome', 'portatore', 'dipendente', 'nome portatore', 'persona'],
            'codice': ['codice', 'cod', 'codice art', 'articolo', 'cod.art'],
            'descrizione': ['descrizione', 'desc', 'articolo', 'descrizione articolo', 'oggetto']
        }
        
        for standard_name, variants in mappings.items():
            for col in current_cols:
                col_clean = col.strip().lower()
                if any(variant in col_clean for variant in variants):
                    column_map[col] = standard_name
                    break
        
        # Applica mapping
        df_renamed = df.rename(columns=column_map)
        
        # Verifica colonne obbligatorie
        required = ['arm', 'nome', 'descrizione']
        missing = [col for col in required if col not in df_renamed.columns]
        
        if missing:
            logger.warning(f"Colonne mancanti dopo normalizzazione PDF: {missing}")
            # Non blocchiamo, potrebbe essere risolto da OCR fallback
        
        return df_renamed
    
    
    def _read_image_ocr(self, path: Path) -> pd.DataFrame:
        """
        Legge immagine/PDF scannerizzato con OCR Mindee.
        
        Args:
            path: Path a immagine o PDF
        
        Returns:
            DataFrame costruito da DeliveryItem estratti
        """
        
        if not self.ocr_available:
            raise ValueError(
                "OCR disabilitato in questa versione 'Clean'.\n"
                "Per favore usa file Excel (.xlsx) o PDF nativi (testo selezionabile)."
            )
        
        # Placeholder per eventuale riattivazione futura
        # delivery_items = self.ocr_engine.process_image(str(path))
        return pd.DataFrame() # Should not be reached
        
        if not delivery_items:
            raise ValueError(
                "OCR non ha trovato dati strutturati nel documento.\n"
                "Verifica la qualità dell'immagine/PDF."
            )
        
        # Converti DeliveryItem → DataFrame
        data = {
            'arm': [item.locker_number or '' for item in delivery_items],
            'nome': [item.employee_name for item in delivery_items],
            'codice': [item.item_code for item in delivery_items],
            'descrizione': [item.item_description for item in delivery_items]
        }
        
        df = pd.DataFrame(data)
        
        logger.info(f"OCR completato: {len(df)} articoli estratti")
        
        return df


# ============================================================================
# FUNZIONE DI CONVENIENZA
# ============================================================================

def read_delivery_file(file_path: str) -> pd.DataFrame:
    """
    Legge file di consegna (Excel, PDF, o immagine) e ritorna DataFrame.
    
    Args:
        file_path: Path al file
    
    Returns:
        DataFrame con colonne standardizzate
    
    Example:
        df = read_delivery_file("bolle.xlsx")
        df = read_delivery_file("bolle.pdf")
        df = read_delivery_file("foto_bolla.jpg")
    """
    reader = UnifiedFileReader()
    return reader.read_file(file_path)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST UNIFIED FILE READER")
    print("=" * 60)
    
    # Test con file Excel esistente
    test_file = Path("Files_progetto/test_bolla.xlsx")
    
    if test_file.exists():
        print(f"\n1. Test lettura Excel: {test_file.name}")
        try:
            df = read_delivery_file(str(test_file))
            print(f"   ✓ Letto: {len(df)} righe, {len(df.columns)} colonne")
            print(f"\nPrime 3 righe:")
            print(df.head(3))
        except Exception as e:
            print(f"   ✗ Errore: {e}")
    else:
        print(f"\n⚠️ File di test non trovato: {test_file}")
    
    print("\n" + "=" * 60)
    print("Per testare PDF, fornisci un PDF e esegui:")
    print("  df = read_delivery_file('path/to/bolla.pdf')")
    print("=" * 60)
