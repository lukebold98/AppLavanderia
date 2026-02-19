"""
XLS Reader Module - Lettore File Excel per Bolle Lavanderia

Questo modulo è responsabile della lettura e validazione dei file Excel (.xlsx, .xls)
contenenti le bolle di consegna lavanderia.

SCOPO DIDATTICO:
- Imparerai come usare pandas per leggere Excel
- Come gestire errori comuni (file mancante, formato errato, colonne sbagliate)
- Come validare dati in ingresso
- Type hints per codice più chiaro

DIPENDENZE:
- pandas: libreria per manipolazione dati
- openpyxl: engine per leggere file .xlsx (usato da pandas)
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Setup logging per debug (vedremo messaggi chiari se qualcosa va storto)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelReaderError(Exception):
    """
    Eccezione personalizzata per errori specifici del lettore Excel.
    
    Perché crearla?
    - Possiamo distinguere errori del nostro codice da errori generici di Python
    - Messaggi di errore più chiari per l'utente finale
    """
    pass


class XLSReader:
    """
    Classe per leggere file Excel contenenti bolle di consegna.
    
    DESIGN PATTERN: Usiamo una classe per:
    1. Mantenere configurazione (es. nomi colonne accettati)
    2. Riutilizzare metodi di validazione
    3. Gestire stato (cache del file letto)
    
    Esempio d'uso:
        reader = XLSReader()
        df = reader.read_file("bolle.xlsx")
        print(df.head())
    """
    
    # Mapping colonne: accettiamo varianti dei nomi
    # Questo rende il sistema robusto se l'ufficio personale usa nomi diversi
    COLUMN_MAPPINGS = {
        'arm': ['Arm', 'Armadietto', 'ARM', 'arm', 'N.Arm', 'Num.Armadietto'],
        'nome': ['Nome portatore', 'Nome', 'Dipendente', 'nome_portatore', 'NOME'],
        'codice': ['Codice', 'Codice coll.Art.', 'CodiceArt', 'codice_art', 'CODICE'],
        'descrizione': ['Descrizione', 'Desc', 'Articolo', 'descrizione', 'DESC']
    }
    
    # Colonne obbligatorie (se mancano, il file è invalido)
    REQUIRED_COLUMNS = ['arm', 'nome', 'codice', 'descrizione']
    
    
    def __init__(self):
        """
        Inizializza il lettore Excel.
        
        Al momento non serve configurazione extra, ma la struttura è pronta
        per aggiunte future (es. path di default, cache, etc.)
        """
        self.last_read_file: Optional[Path] = None
        self.cached_dataframe: Optional[pd.DataFrame] = None
        logger.info("XLSReader inizializzato con successo")
    
    
    def read_file(self, file_path: str) -> pd.DataFrame:
        """
        Legge un file Excel e restituisce un DataFrame pandas.
        
        Args:
            file_path (str): Percorso al file Excel (relativo o assoluto)
            
        Returns:
            pd.DataFrame: DataFrame con colonne standardizzate
            
        Raises:
            ExcelReaderError: Se il file non esiste, è corrotto, o mancano colonne
        
        Step-by-step process:
        1. Controlla che il file esista
        2. Legge il file con pandas
        3. Valida presenza colonne obbligatorie
        4. Standardizza nomi colonne
        5. Ritorna DataFrame pulito
        """
        
        # STEP 1: Validazione path
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise ExcelReaderError(
                f"File non trovato: {file_path}\n"
                f"Assicurati che il percorso sia corretto."
            )
        
        # STEP 2: Lettura Excel
        try:
            logger.info(f"Lettura file: {file_path}")
            
            # pd.read_excel() fa il lavoro pesante:
            # - Riconosce automaticamente formato (.xlsx vs .xls)
            # - Usa openpyxl come engine per .xlsx
            # - Converte celle in tipi Python appropriati (int, str, date, etc.)
            df = pd.read_excel(file_path, engine='openpyxl')
            
            logger.info(f"File letto con successo: {len(df)} righe, {len(df.columns)} colonne")
            
        except Exception as e:
            # Catturiamo errori generici e li ri-lanciamo come ExcelReaderError
            raise ExcelReaderError(
                f"Errore durante la lettura del file Excel:\n{str(e)}\n"
                f"Il file potrebbe essere corrotto o in un formato non supportato."
            )
        
        # STEP 3: Validazione e standardizzazione colonne
        df_clean = self._validate_and_normalize_columns(df)
        
        # STEP 4: Pulizia dati (rimuovi righe completamente vuote)
        df_clean = self._clean_dataframe(df_clean)
        
        # Cache per uso futuro (opzionale, utile se rileggiamo stesso file)
        self.last_read_file = file_path_obj
        self.cached_dataframe = df_clean
        
        return df_clean
    
    
    def _validate_and_normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida che tutte le colonne obbligatorie siano presenti e le standardizza.
        
        Perché serve?
        - L'ufficio personale potrebbe usare "Armadietto" invece di "Arm"
        - Vogliamo codice che funziona con entrambi
        
        Args:
            df: DataFrame grezzo dal file Excel
            
        Returns:
            DataFrame con colonne standardizzate (sempre: 'arm', 'nome', 'codice', 'descrizione')
        
        Raises:
            ExcelReaderError: Se mancano colonne obbligatorie
        """
        
        # Mappa colonne trovate -> nomi standard
        column_map = {}
        current_columns = df.columns.tolist()
        
        # Per ogni colonna standard che ci serve
        for standard_name, possible_names in self.COLUMN_MAPPINGS.items():
            
            # Cerca se esiste una variante nel file Excel
            found = False
            for col_name in current_columns:
                if col_name in possible_names:
                    column_map[col_name] = standard_name
                    found = True
                    break
            
            # Se non trovata, errore
            if not found and standard_name in self.REQUIRED_COLUMNS:
                raise ExcelReaderError(
                    f"Colonna obbligatoria '{standard_name}' non trovata.\n"
                    f"Colonne presenti nel file: {current_columns}\n"
                    f"Varianti accettate: {possible_names}"
                )
        
        # Applica il mapping (rinomina colonne)
        df_normalized = df.rename(columns=column_map)
        
        # Seleziona solo le colonne che ci servono (ignora eventuali colonne extra)
        df_normalized = df_normalized[self.REQUIRED_COLUMNS]
        
        logger.info(f"Colonne standardizzate: {df_normalized.columns.tolist()}")
        
        return df_normalized
    
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pulisce il DataFrame rimuovendo righe vuote o invalide.
        
        Operazioni:
        1. Rimuove righe completamente vuote
        2. Rimuove righe dove 'arm' o 'nome' sono nulli (dati critici)
        3. Converte 'arm' a intero (se è stringa tipo "19" diventa int 19)
        
        Args:
            df: DataFrame da pulire
            
        Returns:
            DataFrame pulito
        """
        
        # Prima della pulizia
        initial_len = len(df)
        
        # Rimuovi righe completamente vuote
        df = df.dropna(how='all')
        
        # Rimuovi righe dove 'arm' o 'nome' sono vuoti (dati critici)
        df = df.dropna(subset=['arm', 'nome'])
        
        # Converti 'arm' a intero (gestisci caso in cui sia stringa "19.0")
        df['arm'] = df['arm'].astype(int)
        
        # Rimuovi spazi extra nei testi
        df['nome'] = df['nome'].str.strip()
        df['codice'] = df['codice'].astype(str).str.strip()
        df['descrizione'] = df['descrizione'].str.strip()
        
        final_len = len(df)
        
        if initial_len != final_len:
            logger.info(f"Righe rimosse durante pulizia: {initial_len - final_len}")
        
        return df
    
    
    def get_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Genera un riepilogo utile del file Excel letto.
        
        Utile per debug e per mostrare all'utente cosa è stato caricato.
        
        Args:
            df: DataFrame da analizzare
            
        Returns:
            Dizionario con statistiche:
            - num_rows: numero righe
            - num_employees: numero dipendenti unici
            - num_lockers: numero armadietti unici
            - total_items: totale capi
        """
        return {
            'num_rows': len(df),
            'num_employees': df['nome'].nunique(),
            'num_lockers': df['arm'].nunique(),
            'total_items': len(df),
            'employees': df['nome'].unique().tolist(),
            'lockers': sorted(df['arm'].unique().tolist())
        }


# ============================================================================
# FUNZIONE DI CONVENIENZA (per uso semplice senza istanziare classe)
# ============================================================================

def read_excel_file(file_path: str) -> pd.DataFrame:
    """
    Funzione di convenienza per lettura rapida Excel.
    
    Invece di:
        reader = XLSReader()
        df = reader.read_file("file.xlsx")
    
    Puoi fare:
        df = read_excel_file("file.xlsx")
    
    Args:
        file_path: Percorso al file Excel
        
    Returns:
        DataFrame pandas con dati puliti e standardizzati
    """
    reader = XLSReader()
    return reader.read_file(file_path)


# ============================================================================
# TEST AUTOMATICO (esegui questo file direttamente per testare)
# ============================================================================

# ============================================================================
# END OF MODULE
# ============================================================================

