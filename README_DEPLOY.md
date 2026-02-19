# ☁️ Guida al Deploy su Streamlit Cloud

Questa app è ottimizzata per essere ospitata gratuitamente su **Streamlit Community Cloud**.
Questo ti permette di usarla dal cellulare (5G) senza avere il PC acceso.

## 1. Preparazione
Assicurati di aver fatto il "Push" di tutte le modifiche su GitHub. La repository deve contenere:
- `App.py`
- `requirements.txt`
- `.gitignore`
- Cartelle `Modules/`

*(Non deve contenere file `.env` o foto di test)*

## 2. Deploy (Tempo: 2 minuti)
1. Vai su [share.streamlit.io](https://share.streamlit.io/) e accedi con GitHub.
2. Clicca su **"New App"**.
3. Seleziona la repository `AppLavanderia`.
4. Branch: `main` (o master).
5. Main file path: `App.py`.

## 3. Configurazione Segreti (Opzionale)
Se vuoi usare la funzionalità di **OCR per PDF Scannerizzati** (Mindee), devi configurare la chiave API.

1. Nella pagina di deploy, clicca su **"Advanced Settings"**.
2. Copia e incolla questo nel box "Secrets":

```toml
MINDEE_API_KEY = "la-tua-chiave-qui"
```

*(Se non hai la chiave o non ti serve l'OCR, salta questo passaggio. L'app funzionerà comunque per Excel e PDF nativi).*

## 4. Avvio
Clicca **"Deploy!"**.
Dopo circa 1-2 minuti, l'app sarà online.

## 📱 Come usarla dal cellulare
1. Copia l'URL (es. `https://app-lavanderia.streamlit.app`).
2. Invialo su WhatsApp/Telegram a te stesso.
3. Apri il link dal telefono.
4. **Consiglio**: Su iPhone/Android, usa "Aggiungi a Schermata Home" per averla come una vera app.

---

## 🆘 Risoluzione Problemi Comuni

**Errore "Module not found"**
Verifica che il modulo sia elencato in `requirements.txt`.

**Errore "File not found"**
Ricorda che su Cloud non hai i file del tuo PC (es. C:\Users...). L'app può leggere solo i file caricati al momento tramite il tasto Upload.
