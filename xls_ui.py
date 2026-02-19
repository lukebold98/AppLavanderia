import streamlit as st
from typing import List, Optional
import sys
from pathlib import Path
from datetime import datetime
import os
import re

# Import dei moduli interni
sys.path.append(str(Path(__file__).parent))
from Modules.EYES.unified_reader import UnifiedFileReader
from Modules.EYES.xls_parser import XLSParser, DeliveryItem
from Modules.BRAIN.search_controller import SearchController

def sanitize_key(text: str) -> str:
    """Rimuove caratteri speciali che possono rompere i widget di Streamlit."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', text)

def render_xls_workflow():
    st.title("🧺 Gestione Bolle Lavanderia")
    
    # --- STEP 1: CARICAMENTO ---
    uploaded_files = st.file_uploader(
        "1. Carica le bolle (Excel o PDF)",
        type=["xlsx", "xls", "pdf"],
        accept_multiple_files=True,
        key="main_uploader"
    )
    
    if not uploaded_files:
        st.warning("Carica un file per iniziare.")
        st.stop()

    # --- DATI E STATO ---
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
                st.error(f"Errore nel file {f.name}: {e}")
        
        st.session_state.xls_items = all_items
        st.session_state.last_files_key = files_id
        st.session_state.search_controller = SearchController(all_items)
        if "checked_items" not in st.session_state:
            st.session_state.checked_items = set()

    items: List[DeliveryItem] = st.session_state.xls_items
    controller: SearchController = st.session_state.search_controller
    stats = controller.get_stats()
    total_checked = len(st.session_state.checked_items)

    # --- STEP 2: REPORT (Sempre visibile in alto) ---
    st.header("📊 Centro Report")
    with st.container():
        st.write(f"**Progresso: {total_checked} su {stats['total_items']}**")
        st.progress(total_checked / stats["total_items"] if stats["total_items"] > 0 else 0)
        
        if st.button("🚀 GENERA REPORT FINALE", type="primary", use_container_width=True):
            from Modules.EYES.report_generator import ReportGenerator
            gen = ReportGenerator(items, st.session_state.checked_items)
            os.makedirs("temp/reports", exist_ok=True)
            ts = datetime.now().strftime("%H%M")
            pdf_path = f"temp/reports/Report_{ts}.pdf"
            xls_path = f"temp/reports/Report_{ts}.xlsx"
            try:
                gen.generate_pdf(pdf_path)
                gen.generate_excel(xls_path)
                st.session_state.last_report = {"pdf": pdf_path, "xls": xls_path, "text": gen.generate_email_text()}
                st.success("✅ Report PRONTI!")
            except Exception as e:
                st.error(f"Errore: {e}")

        if "last_report" in st.session_state:
            rep = st.session_state.last_report
            with open(rep["pdf"], "rb") as f:
                st.download_button("📄 Scarica PDF", f, os.path.basename(rep["pdf"]), use_container_width=True)
            if st.button("📧 Mostra Testo Email", use_container_width=True):
                st.session_state.show_email = not st.session_state.get("show_email", False)
            if st.session_state.get("show_email"):
                st.text_area("Copia testo", rep["text"], height=150)
        
        if st.button("🔄 Reset tutto", use_container_width=True):
            st.session_state.checked_items = set()
            st.rerun()

    st.divider()

    # --- STEP 3: RICERCA ---
    st.header("🔍 Lista e Ricerca")
    query = st.text_input("Cerca nome o armadietto", placeholder="Esempio: 19")

    # --- STEP 4: VISUALIZZAZIONE ---
    active_items = controller.search(query).items if query else items
    
    if active_items:
        current_employee = ""
        for idx, item in enumerate(active_items):
            # Header dipendente (senza HTML)
            if item.employee_name != current_employee:
                current_employee = item.employee_name
                st.markdown(f"### 👤 {current_employee} (Arm. {item.locker_number or '?'})")
            
            # Checkbox Standard
            item_key = sanitize_key(f"chk_{item.employee_name}_{idx}")
            is_done = item_key in st.session_state.checked_items
            
            # La label contiene tutto il testo, così l'area cliccabile è grande
            label = f"{item.item_description}"
            if is_done:
                label = f"✅ {label} (OK)"
            
            check = st.checkbox(label, value=is_done, key=item_key)
            
            if check: st.session_state.checked_items.add(item_key)
            else: st.session_state.checked_items.discard(item_key)
    else:
        st.info("Nessun articolo trovato.")

if __name__ == "__main__":
    render_xls_workflow()
