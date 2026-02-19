"""
Search Controller Module - Ricerca Veloce per Armadietti e Dipendenti

Questo modulo implementa la logica di ricerca che renderà il tuo lavoro 
del venerdì super veloce: digiti "19" e vedi immediatamente tutti i capi 
dell'armadietto 19.

SCOPO DIDATTICO:
- Imparerai algoritmi di ricerca efficienti (O(1) con hash tables)
- Pattern di caching per performance
- Fuzzy search (ricerca tollerante a errori di battitura)
- Design di API pulite e intuitive

PERFORMANCE TARGET:
- Ricerca per armadietto: <1ms per 400 capi
- Ricerca per nome: <5ms con fuzzy matching
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import logging
from difflib import SequenceMatcher

# Import DeliveryItem dalla struttura esistente
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from EYES.xls_parser import DeliveryItem

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# RESULT CLASSES - Strutture Dati per Risultati
# ============================================================================

@dataclass
class SearchResult:
    """
    Risultato di una singola ricerca.
    
    Contiene sia i dati trovati che metadata utili per l'UI.
    """
    query: str                          # Cosa hai cercato (es. "19")
    items: List[DeliveryItem]          # Capi trovati
    total_items: int                    # Numero totale trovato
    search_type: str                    # "locker" o "employee"
    
    @property
    def is_empty(self) -> bool:
        """Controlla se la ricerca ha trovato qualcosa."""
        return len(self.items) == 0
    
    def __str__(self) -> str:
        """Rappresentazione leggibile per debug."""
        if self.is_empty:
            return f"Nessun risultato per '{self.query}'"
        return f"{self.total_items} capi trovati per {self.search_type} '{self.query}'"


# ============================================================================
# SEARCH CONTROLLER
# ============================================================================

class SearchController:
    """
    Controller per ricerche veloci su lista di DeliveryItem.
    
    PERFORMANCE:
    - Usa dizionari (hash tables) per ricerca O(1)
    - Cache i raggruppamenti per evitare ricalcoli
    - Fuzzy search opzionale per tollerare typo
    
    DESIGN:
    - Stateful: mantiene indici in memoria dopo inizializzazione
    - Thread-safe: nessuna modifica dei dati, solo lettura
    - Lazy initialization: indici creati solo quando servono
    
    Esempio d'uso:
        controller = SearchController(items)
        result = controller.search_by_locker("19")
        
        for item in result.items:
            print(f"- {item.item_description}")
    """
    
    def __init__(self, items: List[DeliveryItem]):
        """
        Inizializza il controller con la lista di capi.
        
        Args:
            items: Lista completa di DeliveryItem da rendere ricercabili
        
        Note:
            Gli indici vengono creati "lazy" (quando servono), non subito.
            Questo rende l'inizializzazione istantanea anche con molti dati.
        """
        self.items = items
        
        # Cache: indici per ricerca veloce (creati on-demand)
        self._locker_index: Optional[Dict[str, List[DeliveryItem]]] = None
        self._employee_index: Optional[Dict[str, List[DeliveryItem]]] = None
        
        # Stats per debugging
        self._search_count = 0
        
        logger.info(f"SearchController inizializzato con {len(items)} articoli")
    
    
    # ========================================================================
    # PUBLIC API - Metodi principali
    # ========================================================================
    
    def search_by_locker(self, locker_number: str) -> SearchResult:
        """
        Cerca tutti i capi di un armadietto specifico.
        
        QUESTO È IL METODO CHE USERAI DI PIÙ!
        Scenario: Prendi busta con "19" scritto sopra, digiti "19", 
                  vedi tutti i capi di VILLA NANCY.
        
        Args:
            locker_number: Numero armadietto (es. "19", "5")
        
        Returns:
            SearchResult con tutti i capi trovati
        
        Performance: O(1) - costante, indipendente dal numero di capi totali
        """
        
        # Incrementa contatore ricerche (per stats)
        self._search_count += 1
        
        # Assicurati che l'indice esista
        if self._locker_index is None:
            self._build_locker_index()
        
        # Normalizza input (rimuovi spazi, uppercase se serve)
        normalized_locker = str(locker_number).strip()
        
        # Ricerca nell'indice (O(1) grazie a dizionario!)
        found_items = self._locker_index.get(normalized_locker, [])
        
        # Log per debug
        logger.debug(f"Ricerca armadietto '{normalized_locker}': {len(found_items)} risultati")
        
        return SearchResult(
            query=locker_number,
            items=found_items,
            total_items=len(found_items),
            search_type="locker"
        )
    
    
    def search_by_employee(self, employee_name: str, fuzzy: bool = False) -> SearchResult:
        """
        Cerca tutti i capi di un dipendente specifico.
        
        Scenario: Vuoi vedere cosa ha ricevuto CORTI ELENA questa settimana.
        
        Args:
            employee_name: Nome dipendente (es. "VILLA NANCY")
            fuzzy: Se True, tollera piccoli errori (es. "VILA NANCY" trova "VILLA NANCY")
        
        Returns:
            SearchResult con tutti i capi del dipendente
        
        Performance: 
            - Exact match: O(1)
            - Fuzzy match: O(n) dove n = numero dipendenti (non capi)
        """
        
        self._search_count += 1
        
        # Assicurati che l'indice esista
        if self._employee_index is None:
            self._build_employee_index()
        
        # Normalizza input
        normalized_name = employee_name.strip().upper()
        
        # Prova ricerca esatta prima (velocissima)
        found_items = self._employee_index.get(normalized_name, [])
        
        # Se fuzzy è abilitato e non hai trovato niente con exact match
        if fuzzy and len(found_items) == 0:
            found_items = self._fuzzy_search_employee(normalized_name)
        
        logger.debug(f"Ricerca dipendente '{normalized_name}': {len(found_items)} risultati")
        
        return SearchResult(
            query=employee_name,
            items=found_items,
            total_items=len(found_items),
            search_type="employee"
        )
    
    
    def search(self, query: str, auto_detect: bool = True) -> SearchResult:
        """
        Ricerca "intelligente" che capisce automaticamente se cerchi 
        un armadietto (numero) o un dipendente (testo).
        
        Esempio:
            search("19")           → cerca armadietto 19
            search("VILLA NANCY")  → cerca dipendente
        
        Args:
            query: Stringa di ricerca
            auto_detect: Se True, indovina tipo ricerca; altrimenti cerca entrambi
        
        Returns:
            SearchResult
        """
        
        query_clean = query.strip()
        
        # Auto-detect: se è un numero, cerca armadietto
        if auto_detect and query_clean.isdigit():
            return self.search_by_locker(query_clean)
        
        # Auto-detect: se contiene lettere, cerca dipendente
        if auto_detect and any(c.isalpha() for c in query_clean):
            return self.search_by_employee(query_clean, fuzzy=True)
        
        # Fallback: prova entrambi e ritorna quello con più risultati
        locker_result = self.search_by_locker(query_clean)
        employee_result = self.search_by_employee(query_clean, fuzzy=True)
        
        return locker_result if len(locker_result.items) > 0 else employee_result
    
    
    def get_all_lockers(self) -> List[str]:
        """
        Ritorna lista di tutti i numeri armadietto presenti.
        
        Utile per autocomplete o per mostrare "Armadietti disponibili: 5, 19, 23..."
        
        Returns:
            Lista ordinata di numeri armadietto
        """
        if self._locker_index is None:
            self._build_locker_index()
        
        return sorted(self._locker_index.keys(), key=lambda x: int(x) if x.isdigit() else 999)
    
    
    def get_all_employees(self) -> List[str]:
        """
        Ritorna lista di tutti i nomi dipendenti presenti.
        
        Returns:
            Lista alfabetica di nomi
        """
        if self._employee_index is None:
            self._build_employee_index()
        
        return sorted(self._employee_index.keys())
    
    
    def get_stats(self) -> Dict:
        """
        Statistiche utili per debug e performance monitoring.
        
        Returns:
            Dict con: total_items, total_lockers, total_employees, searches_performed
        """
        return {
            "total_items": len(self.items),
            "total_lockers": len(self.get_all_lockers()),
            "total_employees": len(self.get_all_employees()),
            "searches_performed": self._search_count
        }
    
    
    # ========================================================================
    # PRIVATE METHODS - Implementazione interna
    # ========================================================================
    
    def _build_locker_index(self) -> None:
        """
        Costruisce indice armadietto -> lista capi.
        
        Tecnica: Hash table (dizionario Python)
        Complessità: O(n) per costruzione, O(1) per lookup
        
        Esempio risultato:
            {
                "19": [item1, item2, item3],  # 3 capi armadietto 19
                "5": [item4, item5]            # 2 capi armadietto 5
            }
        """
        
        logger.debug("Costruendo indice armadietti...")
        
        self._locker_index = {}
        
        for item in self.items:
            locker = item.locker_number or "UNKNOWN"
            
            if locker not in self._locker_index:
                self._locker_index[locker] = []
            
            self._locker_index[locker].append(item)
        
        logger.info(f"Indice armadietti creato: {len(self._locker_index)} armadietti")
    
    
    def _build_employee_index(self) -> None:
        """
        Costruisce indice dipendente -> lista capi.
        
        Analogamente a _build_locker_index, ma per nomi dipendenti.
        """
        
        logger.debug("Costruendo indice dipendenti...")
        
        self._employee_index = {}
        
        for item in self.items:
            name = item.employee_name.strip().upper()
            
            if name not in self._employee_index:
                self._employee_index[name] = []
            
            self._employee_index[name].append(item)
        
        logger.info(f"Indice dipendenti creato: {len(self._employee_index)} dipendenti")
    
    
    def _fuzzy_search_employee(self, query: str) -> List[DeliveryItem]:
        """
        Ricerca fuzzy per nomi dipendenti.
        
        Usa algoritmo di similarità per trovare match anche con typo.
        Esempio: "VILA NANCY" trova "VILLA NANCY" (manca una L)
        
        Args:
            query: Nome da cercare (già normalizzato uppercase)
        
        Returns:
            Lista di capi del dipendente più simile (threshold > 0.7)
        
        Algoritmo:
            - SequenceMatcher da difflib (Ratcliff/Obershelp pattern recognition)
            - Threshold 0.7 = almeno 70% di similarità
        """
        
        best_match = None
        best_ratio = 0.0
        
        for name in self._employee_index.keys():
            # Calcola similarità (0.0 = completamente diverso, 1.0 = identico)
            ratio = SequenceMatcher(None, query, name).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = name
        
        # Soglia di accettazione: 70% di similarità
        if best_ratio >= 0.7 and best_match:
            logger.debug(f"Fuzzy match: '{query}' → '{best_match}' (similarity {best_ratio:.2f})")
            return self._employee_index[best_match]
        
        return []


# ============================================================================
# FUNZIONI DI CONVENIENZA
# ============================================================================

def quick_search(items: List[DeliveryItem], query: str) -> SearchResult:
    """
    Ricerca rapida senza istanziare controller manualmente.
    
    Utile per test o script veloci.
    
    Args:
        items: Lista di DeliveryItem
        query: Cosa cercare
    
    Returns:
        SearchResult
    """
    controller = SearchController(items)
    return controller.search(query)


# ============================================================================
# TEST AUTOMATICO
# ============================================================================

# ============================================================================
# END OF MODULE
# ============================================================================

