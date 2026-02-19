import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime

# Versione Ultra-Stabile per Mobile (v4.0)
def render_xls_workflow():
    # TITOLO CON VERSIONE (Per essere sicuri di cosa stiamo vedendo)
    st.title("🧺 Gestione Bolle v4.0")
    st.info("💡 Se non vedi 'v4.0' in alto, l'app sta usando una vecchia versione. Ricarica la pagina.")

    # 1. CARICAMENTO
    uploaded_files = st.file_uploader("📂 Carica Bolla (PDF o Excel)", type=["pdf", "xlsx", "xls"], accept_multiple_files=True, key="uploader_v4")
    
    if not uploaded_files:
        st.stop()

    # Logica caricamento (Inclusione moduli)
    from Modules.EYES.unified_reader import UnifiedFileReader
    from Modules.EYES.xls_parser import XLSParser
    from Modules.BRAIN.search_controller import SearchController

    # Identificativo file carichi
    files_id = ",".join([f"{f.name}_{f.size}" for f in uploaded_files])

    if "xls_items" not in st.session_state or st.session_state.get("last_files_key") != files_id:
        all_items = []
        for f in uploaded_files:
            try:
                reader = UnifiedFileReader()
                df = reader.read_file(f, filename=f.name)
                parser = XLSParser(deduplicate=False)
                all_items.extend(parser.parse(df))
            except Exception as e:
                st.error(f"Errore caricamento: {e}")
        
        st.session_state.xls_items = all_items
        st.session_state.last_files_key = files_id
        st.session_state.search_controller = SearchController(all_items)
        if "checked_items" not in st.session_state:
            st.session_state.checked_items = set()

    # Recupero dati
    controller = st.session_state.search_controller
    stats = controller.get_stats()

    # 2. CENTRO REPORT (In primo piano)
    with st.expander("📊 OPERAZIONI E REPORT", expanded=True):
        st.write(f"✅ **Spuntati: {len(st.session_state.checked_items)} / {stats['total_items']} capi**")
        st.progress(len(st.session_state.checked_items) / stats["total_items"] if stats["total_items"] > 0 else 0)
        
        if st.button("🚀 GENERA REPORT FINALE", use_container_width=True, type="primary"):
            from Modules.EYES.report_generator import ReportGenerator
            gen = ReportGenerator(st.session_state.xls_items, st.session_state.checked_items)
            os.makedirs("temp/reports", exist_ok=True)
            path = f"temp/reports/rep_{datetime.now().strftime('%H%M')}.pdf"
            gen.generate_pdf(path)
            st.session_state.last_rep_v4 = path
            st.success("Report Generato con successo!")

        if "last_rep_v4" in st.session_state:
            with open(st.session_state.last_rep_v4, "rb") as f:
                st.download_button("📄 SCARICA PDF", f, file_name="Report_Lavanderia.pdf", use_container_width=True)
        
        if st.button("🔄 Reset Totale", use_container_width=True):
            st.session_state.checked_items = set()
            st.rerun()

    # 3. RICERCA
    st.divider()
    query = st.text_input("🔍 Cerca Armadietto o Nome", placeholder="Es: 19 o VILLA")
    
    # 4. LISTA (Checkbox 100% Standard con indici stabili)
    all_items = st.session_state.xls_items
    
    # Filtriamo mantenendo l'indice originale per chiavi stabili
    items_with_indices = []
    for i, item in enumerate(all_items):
        if not query or query.upper() in item.employee_name.upper() or query in (item.locker_number or ""):
            items_with_indices.append((i, item))
    
    curr_emp = ""
    for original_idx, item in items_with_indices:
        if item.employee_name != curr_emp:
            curr_emp = item.employee_name
            st.subheader(f"👤 {curr_emp} (Arm. {item.locker_number or '?'})")
        
        # Chiave univoca STABILE basata sull'indice assoluto
        key_v4 = f"v4_{original_idx}"
        
        # Checkbox nativa
        checked = st.checkbox(
            f"{item.item_description}", 
            value=key_v4 in st.session_state.checked_items, 
            key=key_v4
        )
        
        if checked: st.session_state.checked_items.add(key_v4)
        else: st.session_state.checked_items.discard(key_v4)

if __name__ == "__main__":
    st.set_page_config(page_title="App Lavanderia v4", layout="wide")
    render_xls_workflow()
