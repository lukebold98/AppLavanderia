"""
Report Generator Module - Generazione Report Finali

Questo modulo si occupa di creare i report da inviare all'ufficio personale/lavanderia.
Supporta:
1. PDF Professionale (lista spuntata, header, footer)
2. Excel Annotato (file originale + colonna stato)
3. Testo Semplice (per email veloce)
"""

import pandas as pd
from fpdf import FPDF
from pathlib import Path
from typing import List, Set, Dict, Optional, Any
import logging
import os
from datetime import datetime

# Import DeliveryItem
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from Modules.EYES.xls_parser import DeliveryItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFReport(FPDF):
    """Classe custom per layout PDF coerente"""
    
    def header(self):
        # Logo (se esistesse)
        # self.image('logo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Report Controllo Consegna Lavanderia', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}} - Generato il {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')


class ReportGenerator:
    """
    Generatore di report multi-formato.
    
    Esempio:
        generator = ReportGenerator(items, checked_items_ids)
        pdf_path = generator.generate_pdf("report.pdf")
        xls_path = generator.generate_excel("report.xlsx")
    """
    
    def __init__(self, items: List[DeliveryItem], checked_ids: Set[str]):
        """
        Args:
            items: Lista completa di DeliveryItem elaborati
            checked_ids: Set di ID univoci degli articoli spuntati (consegnati)
        """
        self.items = items
        self.checked_ids = checked_ids
        
        # Mappa items con stato
        self.enriched_items = []
        for idx, item in enumerate(items):
            # Ricostruisce ID usato nell'UI
            item_id = f"{item.employee_name}_{item.item_code}_{idx}"
            is_checked = item_id in checked_ids
            
            self.enriched_items.append({
                "item": item,
                "status": "CONSEGNATO" if is_checked else "MANCANTE",
                "is_checked": is_checked
            })

    def _clean_text(self, text: str) -> str:
        """Rimuove caratteri non compatibili con Latin-1 (fpdf 1.7.2)"""
        if not text:
            return ""
        # Sostituzioni comuni per simboli tipografici che rompono Latin-1
        replacements = {
            '\u2019': "'", # Smart quote single
            '\u2018': "'",
            '\u201c': '"', # Smart quote double
            '\u201d': '"',
            '\u2013': "-", # En dash
            '\u2014': "-", # Em dash
            '\u2022': "*", # Bullet
            '\u2026': "...", # Ellipsis
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
            
        # Fallback estremo: encode e decode per scartare caratteri impossibili
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, output_path: str) -> str:
        """Genera report PDF professionale."""
        pdf = PDFReport()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_font('Arial', '', 12)
        
        # Info Generali
        completed = sum(1 for x in self.enriched_items if x['is_checked'])
        total = len(self.enriched_items)
        pdf.set_font('Arial', 'B', 12)
        header_text = self._clean_text(f"Riepilogo Consegna: {completed}/{total} articoli consegnati")
        pdf.cell(0, 10, header_text, 0, 1)
        pdf.ln(5)
        
        # Raggruppa per dipendente
        grouped = {}
        for entry in self.enriched_items:
            emp = entry['item'].employee_name
            if emp not in grouped:
                grouped[emp] = []
            grouped[emp].append(entry)
            
        # Itera dipendenti
        for emp, entries in grouped.items():
            locker = entries[0]['item'].locker_number or "N/A"
            clean_emp = self._clean_text(f"{emp} (Armadietto {locker})")
            
            # Header Dipendente
            pdf.set_fill_color(230, 240, 255) # Azzurro chiaro
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, clean_emp, 1, 1, 'L', fill=True)
            
            # Lista Articoli
            pdf.set_font('Arial', '', 10)
            for entry in entries:
                item = entry['item']
                status_icon = "[X]" if entry['is_checked'] else "[ ]"
                status_text = "OK" if entry['is_checked'] else "MANCANTE"
                
                # Colore testo base
                pdf.set_text_color(0, 0, 0)
                if not entry['is_checked']:
                    pdf.set_text_color(200, 0, 0) # Rosso per mancanti
                
                line = self._clean_text(f"  {status_icon} {item.item_description} ({status_text})")
                pdf.cell(0, 6, line, 0, 1)
            
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0) # Reset nero
            
        output_file = Path(output_path)
        pdf.output(str(output_file), 'F')
        return str(output_file)

    def generate_excel(self, output_path: str) -> str:
        """Genera Excel con formattazione condizionale."""
        data = []
        for entry in self.enriched_items:
            item = entry['item']
            data.append({
                "Armadietto": item.locker_number,
                "Dipendente": item.employee_name,
                "Descrizione": item.item_description,
                "Quantità": item.quantity,
                "Stato Consegna": entry['status']
            })
            
        df = pd.DataFrame(data)
        
        # Salva Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        # TODO: Aggiungere formattazione colori con openpyxl se richiesto
        # Per ora Excel semplice è sufficiente
        
        return output_path

    def generate_email_text(self) -> str:
        """Genera testo semplice per email."""
        completed = sum(1 for x in self.enriched_items if x['is_checked'])
        total = len(self.enriched_items)
        missing_count = total - completed
        
        lines = [
            f"REPORT CONSEGNA LAVANDERIA - {datetime.now().strftime('%d/%m/%Y')}",
            f"Totale Articoli: {total}",
            f"Consegnati: {completed}",
            f"Mancanti: {missing_count}",
            "-----------------------------------"
        ]
        
        # Elenca solo i mancanti se ci sono, per brevità
        if missing_count > 0:
            lines.append("\nARTICOLI MANCANTI/NON CONSEGNATI:")
            for entry in self.enriched_items:
                if not entry['is_checked']:
                    item = entry['item']
                    lines.append(f"- {item.employee_name}: {item.item_description}")
        else:
            lines.append("\n✅ TUTTI GLI ARTICOLI CONSEGNATI CORRETTAMENTE.")
            
        return "\n".join(lines)


if __name__ == "__main__":
    # Test Rapido
    from Modules.EYES.xls_parser import DeliveryItem
    
    # Dati fake
    items = [
        DeliveryItem("ROSSI MARIO", "123", "Giacca", 1, "10"),
        DeliveryItem("BIANCHI LUIGI", "456", "Pantalone", 1, "12"),
        DeliveryItem("BIANCHI LUIGI", "789", "Camicia", 1, "12")
    ]
    checked = {"ROSSI MARIO_123_0", "BIANCHI LUIGI_789_2"} # Manca il pantalone
    
    gen = ReportGenerator(items, checked)
    print("Test Text:\n", gen.generate_email_text())
    
    # Crea PDF test
    gen.generate_pdf("test_report.pdf")
    print("\nPDF generato: test_report.pdf")
    
    # Crea Excel test
    gen.generate_excel("test_report.xlsx")
    print("Excel generato: test_report.xlsx")
