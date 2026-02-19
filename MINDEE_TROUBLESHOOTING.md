# Mindee API Troubleshooting Guide

Questo documento riassume i problemi riscontrati durante l'integrazione di Mindee API e come sono stati risolti. Utile come riferimento per futuri aggiornamenti o nuovi modelli.

## 1. Versione SDK (ClientV1 vs ClientV2)
**Problema**: I modelli personalizzati moderni richiedono l'uso del protocollo asincrono.
**Soluzione**: Passaggio da `mindee.Client` a `mindee.ClientV2`.
- **V1**: Usava `enqueue_and_parse` con parametri stringa.
- **V2**: Richiede `enqueue_and_get_inference` con polling automatico integrato.

## 2. Identificazione del Modello
**Problema**: L'identificazione tramite `account_name` e `endpoint_name` (slug) generava errori di autorizzazione (401) o di firma (TypeError).
**Soluzione**: Utilizzo del **Model ID** (UUID) univoco fornito dalla dashboard di Mindee nella sezione "API Request" o "Quick Start".
- Parametro richiesto: `model_id="db544bb0-592a-4275-b0b0-bc5d9fecb597"`.

## 3. Estrazioni Multiple (IMPORTANTE)
**Problema**: L'API restituisce solo un valore anche se nel documento ce ne sono molti.
**Soluzione**: Nella dashboard di Mindee, all'interno dell'editor del modello, cliccare sull'icona dell'ingranaggio di ogni campo e attivare:
- **"Allow multiple values"** (o "Enable multiple extractions").
Senza questa opzione, Mindee filtrerà sempre i risultati restituendo solo quello con il punteggio di confidenza più alto.

## 4. Cambiamenti nella Struttura dei Campi (V2)
L'SDK V2 ha introdotto cambiamenti negli attributi degli oggetti `SimpleField`:

| Attributo Vecchio (V1) | Attributo Nuovo (V2) | Descrizione |
| :--- | :--- | :--- |
| `.values` | `.value` | L'accesso al testo è diventato singolare per i campi semplici. |
| `.str_value` | `.value` | Spesso `.str_value` non è più presente, preferire `.value`. |
| `.polygon` | `.locations[0].polygon` | Le coordinate geometriche sono state nidificate dentro una lista di 'locations'. |

## 4. Configurazione Ambiente (.env)
Assicurarsi che il file `.env` contenga sempre:
- `MINDEE_API_KEY`: Il token API (senza apici o spazi).
- `MINDEE_MODEL_ID`: L'UUID del modello.

## 5. Geometric Reconstruction (Logica di Business)
Per associare correttamente gli articoli all'addetto in una bolla cartacea:
- Recuperare la coordinata **Y media** (Centroide) di ogni campo.
- Ordinare i campi per Y.
- L'addetto "attivo" per un articolo è l'ultimo apparso con una coordinata Y minore (sopra) rispetto all'articolo stesso.
