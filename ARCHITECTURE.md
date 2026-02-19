# Architecture Decision Record (ADR)

## Contesto del Progetto
Applicazione per la gestione e verifica delle bolle di consegna lavanderia, utilizzata settimanalmente per il controllo di ~40 armadietti con centinaia di capi di vestiario.

---

## Decision 1: In-Memory Processing vs Database-First

### Problema
Quando si carica un file Excel/bolle, bisogna decidere se:
- A) Processare tutto in memoria (liste Python, raggruppamenti con loop)
- B) Salvare immediatamente nel database e fare query SQL (GROUP BY, JOIN, etc.)

### Decisione: **In-Memory Processing** (Approccio A)

### Motivazioni

#### Performance
- **Latency**: Operazioni in RAM sono ~1000x più veloci che query database
- **Volume dati**: 40 armadietti × ~10 capi = 400 record → facilmente gestibile in memoria
- **Ricerca**: Filtrare 400 oggetti Python con list comprehension richiede <1ms

#### Semplicità
- Meno dipendenze infrastrutturali (no server DB, no connessioni)
- Debugging più facile (puoi ispezionare la lista con `print()`)
- Deploy semplificato (basta Python + Streamlit)

#### Workflow Utente
Il caso d'uso è una **sessione singola**:
1. Venerdì mattina: Carica XLS
2. Lavora 30-60 minuti spuntando i capi consegnati
3. Chiude l'app

Non serve persistenza durante il lavoro, serve **velocità di ricerca**.

### Trade-offs Accettati

#### ❌ Cosa perdiamo
- **No storico automatico**: Se chiudi l'app, dati persi (ma vedi "Future Work" sotto)
- **No query complesse**: Non puoi fare `SELECT AVG(items) GROUP BY month` via SQL
- **Limite scalabilità**: Se un giorno avessi 10.000 capi, RAM potrebbe essere insufficiente (ma siamo lontani da questo scenario)

#### ✅ Cosa guadagniamo
- Ricerca "Digitare 19 → vedi armadietto" è **istantanea**
- Codice più leggibile e manutenibile
- Zero overhead di rete o I/O disco durante il lavoro

### Implementazione

Raggruppamento con dizionari Python:
```python
def group_by_locker(items: List[DeliveryItem]) -> Dict[str, List[DeliveryItem]]:
    grouped = {}
    for item in items:
        locker = item.locker_number
        if locker not in grouped:
            grouped[locker] = []
        grouped[locker].append(item)
    return grouped
```

Complessità temporale: **O(n)** dove n = numero capi  
Con 400 capi: ~0.5ms su hardware moderno

### Future Work (se necessario scalare)

Se in futuro servisse storico/analisi, approccio ibrido:
1. **Durante lavoro**: Mantieni in-memory (velocità)
2. **A fine sessione**: Batch insert nel DB con timestamp
3. **Per report storici**: Query SQL offline

```python
# Esempio pattern ibrido
def save_session_to_history(items: List[DeliveryItem]):
    """Chiamata SOLO a fine giornata, non durante il lavoro."""
    session_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    for item in items:
        db.insert("delivery_history", {
            "session_id": session_id,
            "timestamp": timestamp,
            "employee_name": item.employee_name,
            "locker": item.locker_number,
            "item_code": item.item_code,
            "delivered": item.checked
        })
```

---

## Decision 2: Pandas DataFrame come Formato Intermedio

### Problema
Come rappresentare i dati tra lettura Excel e oggetti Python?

### Decisione: **Usare pandas.DataFrame**

### Motivazioni

- **Standardizzazione**: Excel → DataFrame è un pattern consolidato (libreria `openpyxl`)
- **Manipolazione dati**: Pandas offre metodi potenti (`.dropna()`, `.fillna()`, type conversion)
- **Future-proof**: Se domani serve CSV o PDF, pandas supporta entrambi
- **Debugging**: `.head()`, `.info()` rendono facile ispezionare dati

### Alternativa Considerata
**Leggere Excel riga per riga manualmente** con `openpyxl.load_workbook()`

**Perché scartata**: Più codice boilerplate, reinventare la ruota

---

## Decision 3: Streamlit per UI invece di Full Stack (React + FastAPI)

### Problema
Quale tecnologia per l'interfaccia utente?

### Decisione: **Streamlit** (almeno per MVP)

### Motivazioni

#### Velocità di sviluppo
- UI pronta in poche righe: `st.text_input()`, `st.button()`, `st.checkbox()`
- Nessun HTML/CSS/JavaScript da scrivere
- Hot-reload automatico

#### Mobile-Compatible
- Streamlit è responsive di default (funziona su cellulare)
- PWA possibile con configurazione minima

#### Caso d'uso
- **Utente singolo** (o pochi)
- **No autenticazione complessa** (login semplice con password)
- **Deploy locale o Streamlit Cloud** (gratis)

### Quando Passare a FastAPI + React?

Solo se emergono questi requisiti:
- Multi-tenancy con 10+ utenti simultanei
- App mobile nativa (iOS/Android)
- API pubbliche per integrazione sistemi esterni
- Performance critica (Streamlit ha overhead per re-render)

---

## Struttura del Codice

### Design Pattern: **Layered Architecture**

```
📁 Modules/
  ├── EYES/        → Input Layer (lettura dati esterni)
  │   ├── xls_reader.py    # Excel → DataFrame
  │   ├── xls_parser.py    # DataFrame → DeliveryItem
  │   └── ocr_engine.py    # OCR fallback (Mindee)
  │
  ├── BRAIN/       → Business Logic Layer
  │   ├── controller.py        # Orchestrazione generale
  │   └── search_controller.py # Logica ricerca veloce
  │
  └── MEMORY/      → Persistence Layer
      └── database.py  # SQLite per storico (opzionale)
```

**Principio**: Separazione delle responsabilità (Separation of Concerns)
- EYES non sa nulla del DB
- BRAIN non sa come si legge l'Excel
- MEMORY non sa nulla dell'UI

### Vantaggi
- **Testabilità**: Ogni layer si testa indipendentemente
- **Manutenibilità**: Cambio implementazione Excel senza toccare BRAIN
- **Estendibilità**: Aggiungo PDF reader senza modificare parser

---

## Decisioni di Codice

### Type Hints Obbligatori
```python
# ✅ Buono
def parse(df: pd.DataFrame) -> List[DeliveryItem]:
    ...

# ❌ Evitare
def parse(df):
    ...
```

**Motivazione**: Codice più chiaro, auto-completion IDE, catch errori prima del runtime

### Docstring per Ogni Funzione Pubblica
```python
def group_by_locker(items: List[DeliveryItem]) -> Dict[str, List[DeliveryItem]]:
    """
    Raggruppa articoli per numero armadietto.
    
    Args:
        items: Lista di capi da raggruppare
    
    Returns:
        Dizionario {numero_armadietto: [lista_capi]}
    """
```

**Motivazione**: Codice auto-documentante, utile per GitHub collaboratori

### Error Handling Esplicito
```python
# ✅ Buono
try:
    df = pd.read_excel(path)
except FileNotFoundError:
    raise ExcelReaderError(f"File non trovato: {path}")

# ❌ Evitare
df = pd.read_excel(path)  # Silently fail?
```

**Motivazione**: Messaggi di errore chiari per debugging rapido

---

## Licenza e Contributi

Questo progetto è open-source (da definire licenza MIT/Apache).

Contributi benvenuti, ma si prega di:
1. Rispettare l'architettura layered
2. Aggiungere test per nuove feature
3. Documentare scelte architetturali in questo file

---

**Ultima modifica**: 2026-02-05  
**Autore**: [luc21]
