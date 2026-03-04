import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime

# Import moduli interni (ora al top per stabilità)
from Modules.EYES.unified_reader import UnifiedFileReader
from Modules.EYES.xls_parser import XLSParser
from Modules.BRAIN.search_controller import SearchController
from Modules.EYES.report_generator import ReportGenerator

def toggle_item_callback(item_uid):
    """Sincronizza lo stato della checkbox con il set in memoria in tempo reale."""
    # Il valore del widget è accessibile tramite st.session_state[item_uid]
    if st.session_state.get(item_uid, False):
        st.session_state.checked_items.add(item_uid)
    else:
        st.session_state.checked_items.discard(item_uid)

@st.fragment
def render_search_and_list(all_items):
    """Renderizza statistiche, ricerca e lista in un frammento isolato per velocità."""
    
    # 2. STATISTICHE (Ora dentro il fragment per essere reattivo)
    checked_items = st.session_state.checked_items
    total_count = len(all_items)
    
    with st.expander("📊 STATISTICHE E REPORT", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"✅ **Spuntati: {len(checked_items)} / {total_count} capi**")
            progress = len(checked_items) / total_count if total_count > 0 else 0
            st.progress(progress)
        
        with col2:
            if st.button("🔄 Reset Totale", use_container_width=True):
                st.session_state.checked_items = set()
                st.rerun()

        st.divider()
        
        if st.button("🚀 GENERA REPORT FINALE (PDF)", use_container_width=True, type="primary"):
            os.makedirs("temp/reports", exist_ok=True)
            path = f"temp/reports/rep_{datetime.now().strftime('%H%M')}.pdf"
            gen = ReportGenerator(all_items, checked_items)
            gen.generate_pdf(path)
            st.session_state.last_rep_v5 = path
            st.success("Report Generato!")

        if "last_rep_v5" in st.session_state:
            with open(st.session_state.last_rep_v5, "rb") as f:
                st.download_button("📄 SCARICA PDF", f, file_name="Report_Lavanderia.pdf", use_container_width=True)

    st.divider()
    
    # 3. RICERCA
    query = st.text_input("🔍 Cerca Armadietto o Nome (Filtro veloce)", placeholder="Es: 19 o VILLA", key="search_query")
    
    # Filtriamo mantenendo l'indice originale per chiavi stabili via UID
    filtered_items = []
    for item in all_items:
        if not query or query.upper() in item.employee_name.upper() or query in (item.locker_number or ""):
            filtered_items.append(item)
    
    # 4. LISTA
    curr_emp = ""
    for item in filtered_items:
        if item.employee_name != curr_emp:
            curr_emp = item.employee_name
            st.subheader(f"👤 {curr_emp} (Arm. {item.locker_number or '?'})")
        
        # Usa l'UID stabile generato dal parser
        item_uid = item.uid
        
        # Checkbox nativa con callback per aggiornare 'checked_items'
        st.checkbox(
            f"{item.item_description}", 
            value=item_uid in st.session_state.checked_items, 
            key=item_uid,
            on_change=toggle_item_callback,
            args=(item_uid,)
        )

# Versione Ultra-Performante (v5.1)
def render_xls_workflow():
    # TITOLO CON VERSIONE
    st.title("🧺 Gestione Bolle v5.1")
    st.info("💡 Se non vedi 'v5.1' in alto, ricarica la pagina. Questa versione corregge il contatore in tempo reale.")

    # 1. CARICAMENTO
    uploaded_files = st.file_uploader("📂 Carica Bolla (PDF o Excel)", type=["pdf", "xlsx", "xls"], accept_multiple_files=True, key="uploader_v5")
    
    if not uploaded_files:
        if "xls_items" in st.session_state:
            # Pulisci se non ci sono file
            del st.session_state.xls_items
            if "checked_items" in st.session_state:
                st.session_state.checked_items = set()
        st.stop()

    # Identificativo file carichi
    files_id = ",".join([f"{f.name}_{f.size}" for f in uploaded_files])

    # Inizializzazione dati
    if "xls_items" not in st.session_state or st.session_state.get("last_files_key") != files_id:
        all_items = []
        for f in uploaded_files:
            try:
                reader = UnifiedFileReader()
                df = reader.read_file(f, filename=f.name)
                parser = XLSParser(deduplicate=False)
                all_items.extend(parser.parse(df))
            except Exception as e:
                st.error(f"Errore caricamento '{f.name}': {e}")
        
        st.session_state.xls_items = all_items
        st.session_state.last_files_key = files_id
        if "checked_items" not in st.session_state:
            st.session_state.checked_items = set()

    all_items = st.session_state.xls_items

    # 2, 3 & 4. TUTTO NEL FRAGMENT REATTIVO
    render_search_and_list(all_items)

if __name__ == "__main__":
    st.set_page_config(page_title="App Lavanderia v5", layout="wide")
    render_xls_workflow()
