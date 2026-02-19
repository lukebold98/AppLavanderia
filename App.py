
import streamlit as st
from xls_ui import render_xls_workflow

# Configurazione Pagina
st.set_page_config(
    page_title="AppLavanderia - Digital Workflow",
    page_icon="clothes",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS per mobile optimization
st.markdown("""
    <style>
    .stButton>button {
        height: 3rem;
        font-size: 1.2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Main Workflow
render_xls_workflow()

# Sidebar Info
st.sidebar.title("ℹ️ Info")
st.sidebar.info(
    "AppLavanderia v2.0\n"
    "Workflow Digitale (XLS/PDF)\n"
    "\n"
    "Supporto:\n"
    "- Excel (.xlsx)\n"
    "- PDF Native\n"
    "- Foto/Scan (OCR)\n"
)
