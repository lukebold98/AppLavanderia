"""
XLS Parser Module - Convertitore DataFrame → DeliveryItem

Questo modulo prende il DataFrame pulito dal XLSReader e lo trasforma in 
una lista di oggetti DeliveryItem (struttura usata dal resto dell'app).

SCOPO DIDATTICO:
- Imparerai a trasformare dati "grezzi" (DataFrame) in oggetti strutturati
- Come raggruppare dati per armadietto/dipendente
- Pattern di validazione e error handling
- List comprehension e iterazione efficiente

FLUSSO:
DataFrame (pandas) → Validazione → Raggruppamento → List[DeliveryItem]
"""

import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES - Strutture Dati
# ============================================================================

@dataclass
class DeliveryItem:
    """
    Rappresenta un singolo capo di vestiario consegnato.
    """
    employee_name: str              # Nome dipendente (es. "VILLA NANCY")
    item_description: str           # Descrizione (es. "Felpa Essentials...")
    item_code: str = ""             # Codice articolo (opzionale)
    quantity: int = 1               # Quantità (default 1)
    locker_number: Optional[str] = None  # Numero armadietto (es. "19")


class ParserError(Exception):
    """Eccezione per errori specifici del parser."""
    pass


# ============================================================================
# PARSER CLASS
# ============================================================================

class XLSParser:
    """
    Parser per convertire DataFrame pandas in lista di DeliveryItem.
    
    Responsabilità:
    1. Validare dati DataFrame
    2. Raggruppare per dipendente/armadietto
    3. Creare oggetti DeliveryItem
    4. Gestire edge cases (dati mancanti, duplicati, etc.)
    
    Esempio d'uso:
        df = read_excel_file("bolla.xlsx")
        parser = XLSParser()
        items = parser.parse(df)
        print(f"Trovati {len(items)} capi")
    """
    
    def __init__(self, deduplicate: bool = False):
        """
        Inizializza il parser.
        
        Args:
            deduplicate: Se True, rimuove articoli duplicati (stesso nome + codice)
                        Se False, tiene anche i duplicati (utile se ci sono più pezzi uguali)
        """
        self.deduplicate = deduplicate
        logger.info(f"XLSParser inizializzato (deduplicate={deduplicate})")
    
    
    def parse(self, df: pd.DataFrame) -> List[DeliveryItem]:
        """
        Converte DataFrame in lista di DeliveryItem con forward fill e filtrazione.
        """
        # STEP 1: Validazione colonne coinvolte
        self._validate_dataframe(df)
        
        # STEP 2: Pre-processamento (Forward Fill)
        # Se nome o armadietto sono vuoti, usa l'ultimo valore valido
        df = df.copy()
        
        # Termini da escludere (Rumore)
        NON_EMPLOYEE_TERMS = ['HUEGLI', 'ELIS', 'PUNTO CONSEGNA', 'CLIENTE', 'UFFICI', 'TOTALE', 'ZONA', ' GIRO']
        
        items = []
        last_arm = "N/A"
        last_name = "SCONOSCIUTO"
        
        for idx, row in df.iterrows():
            try:
                # Estrai valori correnti
                curr_arm = str(row['arm']).strip() if 'arm' in row and pd.notna(row['arm']) and str(row['arm']).strip() != "" else None
                curr_name = str(row['nome']).strip().upper() if 'nome' in row and pd.notna(row['nome']) and str(row['nome']).strip() != "" else None
                curr_desc = str(row['descrizione']).strip() if 'descrizione' in row and pd.notna(row['descrizione']) else ""
                
                # Se è una riga di rumore, saltala e resetta lo stato se necessario
                is_noise = any(term in str(curr_name or "") for term in NON_EMPLOYEE_TERMS) or \
                           any(term in str(curr_desc or "") for term in NON_EMPLOYEE_TERMS)
                
                if is_noise:
                    continue

                # Forward fill logico: se il campo è vuoto, usa l'ultimo visto
                if curr_arm: last_arm = curr_arm
                if curr_name: last_name = curr_name
                
                # Se non abbiamo nemmeno una descrizione, probabilmente è una riga vuota
                if not curr_desc:
                    continue
                
                # Crea l'oggetto con i dati (reali o propagati)
                item = DeliveryItem(
                    employee_name=last_name,
                    item_description=curr_desc,
                    item_code=str(row.get('codice', '')).strip(),
                    quantity=1,
                    locker_number=last_arm
                )
                
                # Validazione finale dell'item: deve avere un nome credibile (non "SCONOSCIUTO" e non troppo corto)
                if last_name != "SCONOSCIUTO" and len(last_name) > 3:
                    items.append(item)
                
            except Exception as e:
                logger.warning(f"Errore riga {idx}: {e}")
                continue
        
        logger.info(f"Parsing completato: {len(items)} articoli validi trovati")
        
        if self.deduplicate:
            items = self._deduplicate_items(items)
        
        return items
    
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Valida che il DataFrame abbia le colonne necessarie.
        
        Colonne richieste: 'arm', 'nome', 'codice', 'descrizione'
        (Queste sono già standardizzate dal XLSReader)
        
        Args:
            df: DataFrame da validare
        
        Raises:
            ParserError: Se mancano colonne
        """
        required_columns = ['arm', 'nome', 'descrizione']
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            raise ParserError(
                f"DataFrame manca colonne obbligatorie: {missing}\n"
                f"Colonne presenti: {df.columns.tolist()}"
            )
        
        if len(df) == 0:
            raise ParserError("DataFrame è vuoto, nessun dato da parsare.")
    
    
    def _create_delivery_item(self, row: pd.Series) -> DeliveryItem:
        """
        Crea un singolo DeliveryItem da una riga del DataFrame.
        
        Args:
            row: Riga pandas.Series con chiavi: 'arm', 'nome', 'codice', 'descrizione'
        
        Returns:
            DeliveryItem: Oggetto strutturato
        
        Note:
            - row['arm'] → locker_number
            - row['nome'] → employee_name
            - row['codice'] → item_code
            - row['descrizione'] → item_description
        """
        
        # Conversione tipi e pulizia
        locker = str(row['arm']).strip() if 'arm' in row and pd.notna(row['arm']) else "N/A"
        name = str(row['nome']).strip().upper() if 'nome' in row and pd.notna(row['nome']) else "SCONOSCIUTO"
        desc = str(row['descrizione']).strip() if 'descrizione' in row and pd.notna(row['descrizione']) else ""
        code = str(row['codice']).strip() if 'codice' in row and pd.notna(row['codice']) else ""
        
        # Crea oggetto DeliveryItem
        # Nota: quantity default è 1 (definito nella dataclass)
        item = DeliveryItem(
            employee_name=name,
            item_description=desc,
            item_code=code,
            quantity=1,
            locker_number=locker
        )
        
        return item
    
    
    def _deduplicate_items(self, items: List[DeliveryItem]) -> List[DeliveryItem]:
        """
        Rimuove DeliveryItem duplicati.
        
        Due item sono considerati duplicati se hanno:
        - Stesso employee_name
        - Stesso item_code
        - Stesso locker_number
        
        Args:
            items: Lista originale (può avere duplicati)
        
        Returns:
            Lista senza duplicati
        
        Tecnica usata:
        - Usiamo un set() per tracciare combinazioni già viste
        - set() è una struttura dati che NON permette duplicati
        - Molto più veloce di cicli annidati (O(n) invece di O(n²))
        """
        
        seen = set()  # Set di tuple (name, code, locker)
        unique_items = []
        
        for item in items:
            # Crea "firma" univoca dell'item
            signature = (item.employee_name, item.item_code, item.locker_number)
            
            # Se non l'abbiamo mai vista, aggiungi
            if signature not in seen:
                seen.add(signature)
                unique_items.append(item)
        
        duplicates_removed = len(items) - len(unique_items)
        if duplicates_removed > 0:
            logger.info(f"Rimossi {duplicates_removed} duplicati")
        
        return unique_items
    
    
    def group_by_employee(self, items: List[DeliveryItem]) -> Dict[str, List[DeliveryItem]]:
        """
        Raggruppa DeliveryItem per dipendente.
        
        Questo è utile per l'UI: vogliamo mostrare tutti i capi di VILLA NANCY insieme,
        poi tutti quelli di CORTI ELENA, etc.
        
        Args:
            items: Lista di DeliveryItem
        
        Returns:
            Dizionario: {nome_dipendente: [lista_suoi_capi]}
        
        Esempio:
            {
                "VILLA NANCY": [item1, item2, item3],
                "CORTI ELENA": [item4, item5]
            }
        """
        
        grouped: Dict[str, List[DeliveryItem]] = {}
        
        for item in items:
            name = item.employee_name
            
            # Se questo dipendente non è ancora nel dict, crea lista vuota
            if name not in grouped:
                grouped[name] = []
            
            # Aggiungi item alla lista di questo dipendente
            grouped[name].append(item)
        
        logger.info(f"Raggruppati {len(items)} articoli per {len(grouped)} dipendenti")
        
        return grouped
    
    
    def group_by_locker(self, items: List[DeliveryItem]) -> Dict[str, List[DeliveryItem]]:
        """
        Raggruppa DeliveryItem per armadietto.
        
        Utile per la tua ricerca veloce: digiti "19" e vedi tutto l'armadietto 19.
        
        Args:
            items: Lista di DeliveryItem
        
        Returns:
            Dizionario: {numero_armadietto: [lista_capi]}
        
        Esempio:
            {
                "19": [item1, item2, item3],
                "5": [item4, item5]
            }
        """
        
        grouped: Dict[str, List[DeliveryItem]] = {}
        
        for item in items:
            locker = item.locker_number or "SCONOSCIUTO"  # Handle None
            
            if locker not in grouped:
                grouped[locker] = []
            
            grouped[locker].append(item)
        
        logger.info(f"Raggruppati {len(items)} articoli per {len(grouped)} armadietti")
        
        return grouped


# ============================================================================
# FUNZIONE DI CONVENIENZA
# ============================================================================

def parse_delivery_dataframe(df: pd.DataFrame, deduplicate: bool = False) -> List[DeliveryItem]:
    """
    Funzione helper per parsing rapido.
    
    Args:
        df: DataFrame con colonne standardizzate
        deduplicate: Rimuovi duplicati?
    
    Returns:
        List[DeliveryItem]
    """
    parser = XLSParser(deduplicate=deduplicate)
    return parser.parse(df)


# ============================================================================
# END OF MODULE
# ============================================================================

