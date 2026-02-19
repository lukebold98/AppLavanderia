# Mobile-Optimized XLS Workflow Module
# Versione 3.0: Extreme Mobile Compatibility (No Sidebar, No Columns)

import streamlit as st
from typing import List, Optional
import sys
from pathlib import Path
from datetime import datetime
import os

# Import dei nostri moduli XLS
sys.path.append(str(Path(__file__).parent))
from Modules.EYES.unified_reader import UnifiedFileReader
from Modules.EYES.xls_parser import XLSParser, DeliveryItem
from Modules.BRAIN.search_controller import SearchController

def render_xls_workflow():
    st.title("🔍 Spunta Bolle")
    st.markdown("*Ottimizzato per cellulare - Operatività Totale*")

    # ========================================================================
    # STEP 1: Upload File
    # ========================================================================
    uploaded_files = st.file_uploader(
        "1️⃣ Carica Bolle (Excel, PDF, Immagini)",
        type=["xlsx", "xls", "pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if not uploaded_files:
        st.info("👆 Carica i file delle bolle per iniziare.")
        st.stop()

    # ========================================================================
    # STEP 2: Parsing & Session State
    # ========================================================================
    current_files_key = ",".join([f"{f.name}_{f.size}" for f in uploaded_files])
    
    if "xls_items" not in st.session_state or st.session_state.get("last_files_key") != current_files_key:
        all_items = []
        errors = []
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"📖 Lettura {uploaded_file.name}...")
            try:
                reader = UnifiedFileReader()
                df = reader.read_file(uploaded_file, filename=uploaded_file.name)
                parser = XLSParser(deduplicate=False)
                items = parser.parse(df)
                all_items.extend(items)
            except Exception as e:
                errors.append(f"{uploaded_file.name}: {str(e)}")
        
        status_text.empty()
        if errors:
            with st.expander("⚠️ Errori caricamento"):
                for err in errors: st.error(err)
        
        st.session_state.xls_items = all_items
        st.session_state.last_files_key = current_files_key
        st.session_state.search_controller = SearchController(all_items)
        if "checked_items" not in st.session_state:
            st.session_state.checked_items = set()

    items: List[DeliveryItem] = st.session_state.xls_items
    controller: SearchController = st.session_state.search_controller
    stats = controller.get_stats()
    total_checked = len(st.session_state.checked_items)

    # ========================================================================
    # STEP 3: CENTRO REPORT (Spostato dalla Sidebar alla Pagina Principale)
    # ========================================================================
    with st.expander("📊 2️⃣ CENTRO REPORT & DOWNLOAD", expanded=False):
        progress_pct = int((total_checked / stats["total_items"]) * 100) if stats["total_items"] > 0 else 0
        st.write(f"📊 **Progresso: {total_checked} / {stats['total_items']} ({progress_pct}%)**")
        st.progress(progress_pct / 100)
        
        if st.button("🚀 GENERA REPORT FINALE", type="primary", use_container_width=True):
            from Modules.EYES.report_generator import ReportGenerator
            gen = ReportGenerator(items, st.session_state.checked_items)
            os.makedirs("temp/reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            pdf_path = f"temp/reports/Report_{timestamp}.pdf"
            try:
                gen.generate_pdf(pdf_path)
                xls_path = f"temp/reports/Report_{timestamp}.xlsx"
                gen.generate_excel(xls_path)
                st.session_state.last_report = {"pdf": pdf_path, "xls": xls_path, "text": gen.generate_email_text()}
                st.success("✅ Report PRONTI!")
            except Exception as e:
                st.error(f"❌ Errore: {str(e)}")

        if "last_report" in st.session_state:
            rep = st.session_state.last_report
            with open(rep["pdf"], "rb") as f:
                st.download_button("📄 SCARICA PDF", data=f, file_name=os.path.basename(rep["pdf"]), use_container_width=True)
            with open(rep["xls"], "rb") as f:
                st.download_button("📊 SCARICA EXCEL", data=f, file_name=os.path.basename(rep["xls"]), use_container_width=True)
            if st.button("📧 MOSTRA TESTO EMAIL", use_container_width=True):
                st.session_state.show_email_text = not st.session_state.get("show_email_text", False)
            if st.session_state.get("show_email_text"):
                st.text_area("Copia testo email", value=rep["text"], height=200)

        st.divider()
        if st.button("🔄 RESET TUTTE LE SPUNTE", use_container_width=True):
            st.session_state.checked_items = set()
            if "last_report" in st.session_state: del st.session_state.last_report
            st.rerun()

    # ========================================================================
    # STEP 4: RICERCA E LISTA
    # ========================================================================
    st.write("")
    search_query = st.text_input(
        "3️⃣ Cerca Armadietto o Nome",
        placeholder="Es: 19 o VILLA",
        key="search_input"
    )

    # CSS CSS per rendere tutto gigante e visibile
    st.markdown("""
        <style>
        /* Checkbox GIGANTI e Testo GIGANTE */
        .stCheckbox label p {
            font-size: 1.3rem !important;
            font-weight: bold !important;
            padding: 10px 0 !important;
        }
        /* Spazio extra per il tocco */
        .stCheckbox {
            padding: 15px 10px !important;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
            margin-bottom: 5px !important;
        }
        /* Banner dipendente chiaro */
        .employee-banner {
            background: #1f77b4;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0 10px 0;
            font-weight: bold;
            font-size: 1.1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Filtro risultati
    if search_query:
        result = controller.search(search_query)
        display_items = result.items
    else:
        display_items = items

    # Rendering Lista
    if display_items:
        grouped = {}
        for item in display_items:
            if item.employee_name not in grouped: grouped[item.employee_name] = []
            grouped[item.employee_name].append(item)

        for employee, emp_items in grouped.items():
            locker = emp_items[0].locker_number or "N/A"
            st.markdown(f'<div class="employee-banner">👤 {employee} - 📍 {locker}</div>', unsafe_allow_html=True)
            
            for idx, item in enumerate(emp_items):
                item_id = f"{item.employee_name}_{item.item_code}_{idx}"
                
                # Checkbox con etichetta integrata (Massima stabilità)
                desc = item.item_description
                if item_id in st.session_state.checked_items:
                    label = f"✅ ~~{desc}~~"
                else:
                    label = f"⬜ **{desc}**"
                
                is_checked = st.checkbox(
                    label,
                    value=item_id in st.session_state.checked_items,
                    key=f"check_{item_id}"
                )
                
                if is_checked: st.session_state.checked_items.add(item_id)
                else: st.session_state.checked_items.discard(item_id)

    st.write(f"\n*Statistiche: {total_checked}/{stats['total_items']} capi spuntati*")

if __name__ == "__main__":
    st.set_page_config(layout="centered")
    render_xls_workflow()
