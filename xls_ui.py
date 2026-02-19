# Mobile-Optimized XLS Workflow Module
# 
# Questo modulo aggiunge una tab dedicata al caricamento XLS ottimizzata per mobile.
# L'OCR esistente rimane disponibile come backup.

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
    """
    Renderizza l'interfaccia XLS-based per il workflow del venerdì.
    
    Features:
    - Upload XLS/PDF/Immagini (supporto universale!)
    - Barra ricerca gigante mobile-friendly
    - Risultati con checkbox grandi per tap
    - Contatore progressi
    """
    
    st.title("🔍 Ricerca Veloce Bolle")
    st.markdown("*Ottimizzato per cellulare - Supporta Excel, PDF, e Immagini*")
    
    # ========================================================================
    # STEP 1: Upload File
    # ========================================================================
    
    st.subheader("1️⃣ Carica File")
    
    uploaded_files = st.file_uploader(
        "Trascina qui Excel, PDF, o Immagini dall'email (anche multipli)",
        type=["xlsx", "xls", "pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Formati supportati: Excel (.xlsx, .xls), PDF, Immagini (.jpg, .png)"
    )
    
    if not uploaded_files:
        st.info("👆 Carica uno o più file per iniziare\n\n**Formati accettati**:\n- 📊 Excel (.xlsx, .xls)\n- 📄 PDF (nativo o scannerizzato)\n- 📸 Immagini (.jpg, .png)")
        st.stop()
    
    # ========================================================================
    # STEP 2: Parsing File
    # ========================================================================
    
    # Genera una chiave univoca per il set di file caricati (nomi e dimensioni)
    current_files_key = ",".join([f"{f.name}_{f.size}" for f in uploaded_files])
    
    # Usa session_state per cachare i dati
    if "xls_items" not in st.session_state or st.session_state.get("last_files_key") != current_files_key:
        
        all_items = []
        errors = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"📖 Elaborazione file {i+1}/{len(uploaded_files)}: {uploaded_file.name}...")
            
            try:
                # Leggi con unified reader DIRETTAMENTE DAL BUFFER (no disk!)
                reader = UnifiedFileReader()
                df = reader.read_file(uploaded_file, filename=uploaded_file.name)
                
                parser = XLSParser(deduplicate=False)
                items = parser.parse(df)
                all_items.extend(items)
                
            except ValueError as e:
                errors.append(f"{uploaded_file.name}: {str(e)}")
            except Exception as e:
                errors.append(f"{uploaded_file.name}: Errore imprevisto {str(e)}")
            
            # Aggiorna barra progresso
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.empty()
        progress_bar.empty()
        
        if errors:
            with st.expander("⚠️ Alcuni file non sono stati caricati correttamente", expanded=True):
                for err in errors:
                    st.error(err)
            
            if not all_items:
                st.error("❌ Nessun dato valido estratto. Verifica i file.")
                st.stop()
        
        # Salva in session state
        st.session_state.xls_items = all_items
        st.session_state.last_files_key = current_files_key
        st.session_state.search_controller = SearchController(all_items)
        
        # Inizializza stato checkbox se serve
        if "checked_items" not in st.session_state:
            st.session_state.checked_items = set()
            
        # Calcola numero dipendenti unici
        unique_employees = {item.employee_name for item in all_items}
        st.success(f"✅ Caricati {len(all_items)} articoli di {len(unique_employees)} dipendenti da {len(uploaded_files)} file")
    
    # Recupera dati da session state
    items: List[DeliveryItem] = st.session_state.xls_items
    controller: SearchController = st.session_state.search_controller
    
    # ========================================================================
    # SIDEBAR: Report & Azioni (Sempre visibile)
    # ========================================================================
    with st.sidebar:
        st.header("📊 Centro Report")
        
        # Statistiche rapide
        stats = controller.get_stats()
        total_checked = len(st.session_state.checked_items)
        progress_pct = int((total_checked / stats["total_items"]) * 100) if stats["total_items"] > 0 else 0
        
        st.metric("✅ Capi Spuntati", f"{total_checked} / {stats['total_items']}", f"{progress_pct}%")
        st.progress(progress_pct / 100)
        
        st.divider()
        
        # Bottone Generazione Report
        if st.button("🚀 Genera Report Finale", type="primary", use_container_width=True, help="Crea PDF ed Excel con i dati spuntati"):
            # Import on demand
            from Modules.EYES.report_generator import ReportGenerator
            import os
            
            # Prepara dati
            gen = ReportGenerator(items, st.session_state.checked_items)
            
            # Crea cartella temp
            os.makedirs("temp/reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            # 1. Genera PDF (con fix Unicode)
            pdf_path = f"temp/reports/Report_Consegna_{timestamp}.pdf"
            try:
                gen.generate_pdf(pdf_path)
                
                # 2. Genera Excel
                xls_path = f"temp/reports/Report_Consegna_{timestamp}.xlsx"
                gen.generate_excel(xls_path)
                
                # 3. Genera Testo Email
                email_text = gen.generate_email_text()
                
                st.session_state.last_report = {
                    "pdf": pdf_path,
                    "xls": xls_path,
                    "text": email_text
                }
                st.success("✅ Report PRONTI!")
            except Exception as e:
                st.error(f"❌ Errore generazione: {str(e)}")

        # Mostra bottoni download se report è stato generato
        if "last_report" in st.session_state:
            rep = st.session_state.last_report
            import os
            
            with open(rep["pdf"], "rb") as f:
                st.download_button("📄 Scarica PDF", data=f, file_name=os.path.basename(rep["pdf"]), use_container_width=True)
            
            with open(rep["xls"], "rb") as f:
                st.download_button("📊 Scarica Excel", data=f, file_name=os.path.basename(rep["xls"]), use_container_width=True)
            
            if st.button("📧 Testo Email", use_container_width=True):
                st.session_state.show_email_text = not st.session_state.get("show_email_text", False)

        st.divider()
        if st.button("🔄 Reset Totale", use_container_width=True, help="Pulisce tutte le spunte"):
            st.session_state.checked_items = set()
            if "last_report" in st.session_state: del st.session_state.last_report
            st.rerun()

    # ========================================================================
    # STEP 3: Statistiche Rapide (Main Area)
    # ========================================================================
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🎽 Totale Capi", stats["total_items"])
    with col2:
        st.metric("👥 Dipendenti", stats["total_employees"])
    with col3:
        st.metric("✅ Completati", f"{total_checked}/{stats['total_items']}")
    
    st.divider()
    
    # ========================================================================
    # STEP 4: BARRA RICERCA GIGANTE (Mobile-Optimized)
    # ========================================================================
    
    st.subheader("2️⃣ Cerca Armadietto o Dipendente")
    
    # Container per ricerca con styling custom (grandezza aumentata)
    search_query = st.text_input(
        "🔎 Ricerca",
        placeholder="Digita numero armadietto (es. 19) o nome dipendente",
        key="search_input",
        label_visibility="collapsed",  # Nasconde label per più spazio
        help="Esempi: '19', 'VILLA NANCY', 'CORTI'"
    )
    
    # CSS custom per ingrandire input su mobile
    st.markdown("""
        <style>
        /* Ingrandisci input per tap facile */
        input[type="text"] {
            font-size: 1.2rem !important;
            padding: 1rem !important;
            height: 3.5rem !important;
        }
        
        /* Checkbox più grandi per tap */
        .stCheckbox {
            transform: scale(1.5);
            margin-right: 1rem;
        }
        
        /* Card risultati con padding generoso */
        .result-card {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0.5rem;
            background: #f0f2f6;
        }
        
        /* Banner dipendente più visibile */
        .employee-banner {
            background: linear-gradient(90deg, #1f77b4, #4dabf7);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-size: 1.1rem;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ========================================================================
    # STEP 5: Mostra Risultati o Lista Completa
    # ========================================================================
    
    st.subheader("3️⃣ Lista Articoli")
    
    # Se c'è una ricerca, filtra risultati
    if search_query and search_query.strip():
        result = controller.search(search_query.strip())
        
        if result.is_empty:
            st.warning(f"🔍 Nessun risultato per '{search_query}'")
            st.info("💡 Suggerimento: Prova con solo il numero armadietto o le prime lettere del nome")
        else:
            st.success(f"🎯 {result.total_items} articoli trovati")
            display_items = result.items
    else:
        # Nessuna ricerca: mostra tutto raggruppato per dipendente
        display_items = items
    
    # ========================================================================
    # STEP 6: Rendering Lista con Checkbox
    # ========================================================================
    
    if display_items:
        # Raggruppa per dipendente per UI più chiara
        grouped = {}
        for item in display_items:
            name = item.employee_name
            if name not in grouped:
                grouped[name] = []
            grouped[name].append(item)
        
        # Rendering per ogni dipendente
        for employee_name, employee_items in grouped.items():
            
            # Banner dipendente (stile come nella tua UI attuale)
            locker = employee_items[0].locker_number or "N/A"
            
            st.markdown(
                f'<div class="employee-banner">👤 {employee_name} - 📍 Armadietto {locker}</div>',
                unsafe_allow_html=True
            )
            
            # Lista capi di questo dipendente
            for idx, item in enumerate(employee_items):
                
                # ID univoco per checkbox (nome + codice + idx per gestire duplicati)
                item_id = f"{item.employee_name}_{item.item_code}_{idx}"
                
                # Layout: checkbox grande a sinistra, testo a destra
                col_check, col_text = st.columns([1, 5])
                
                with col_check:
                    is_checked = st.checkbox(
                        "OK",
                        value=item_id in st.session_state.checked_items,
                        key=f"check_{item_id}",
                        label_visibility="collapsed"
                    )
                    
                    # Aggiorna set dei checked items
                    if is_checked:
                        st.session_state.checked_items.add(item_id)
                    else:
                        st.session_state.checked_items.discard(item_id)
                
                with col_text:
                    # Mostra solo descrizione
                    display_text = f"{item.item_description}"
                    
                    # Se spuntato, mostra con strikethrough
                    if is_checked:
                        st.markdown(f"~~{display_text}~~", help="Già consegnato")
                    else:
                        st.markdown(display_text)
            
            st.divider()  # Separatore tra dipendenti
    
    # ========================================================================
    # STEP 7: Email Text Area (Se attivato dalla sidebar)
    # ========================================================================
    if st.session_state.get("show_email_text") and "last_report" in st.session_state:
        st.divider()
        st.subheader("📋 Testo per Email")
        st.text_area("Copia questo testo", value=st.session_state.last_report["text"], height=300)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Test standalone
    st.set_page_config(
        page_title="XLS Workflow - AppLaundry",
        page_icon="📊",
        layout="wide"
    )
    
    render_xls_workflow()
