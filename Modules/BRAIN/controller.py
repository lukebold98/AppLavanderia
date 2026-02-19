from typing import List, Optional, Tuple, Any
import pandas as pd
import sqlite3
import os

from Modules.EYES.ocr_engine import OcrEngine, BolleParser, DeliveryItem, MindeeOcrEngine
from Modules.MEMORY.database import DatabaseManager

class DeliveryController:
    """
    Manages the business logic for the Laundry App.
    Acts as the bridge between the Streamlit UI, the OCR Engine, and the Database.
    """
    def __init__(self, db_path: str = "Data/AppLavanderia.db"):
        self.db_path = db_path
        # self.ocr_engine = OcrEngine() # Legacy Tesseract
        # self.parser = BolleParser() # Legacy Parser
        
        # New Mindee Engine
        try:
            self.ocr_engine = MindeeOcrEngine()
            self.use_mindee = True
        except Exception as e:
            print(f"Warning: Failed to init Mindee ({e}). Falling back creates issues as legacy is disabled.")
            self.use_mindee = False
            # Ideally we might fallback to Tesseract here if we wanted
            
        self.db = DatabaseManager(db_path)
        # Ensure schema exists
        self.db.create_schema()

    def process_bolla(self, image_path: str) -> Tuple[str, List[DeliveryItem]]:
        """
        Process a delivery note image.
        Uses Mindee to extract structured data directly.
        
        Returns:
            Tuple containing:
            - Text summary (for debugging/download)
            - List of DeliveryItem objects
        """
        # 1. Process with Mindee
        items = self.ocr_engine.process_image(image_path)
        
        # 2. Generate a text summary of what was found (to replace raw OCR text)
        text_summary = "--- ESTRAZIONE MINDEE ---\n"
        current_emp = ""
        for item in items:
            if item.employee_name != current_emp:
                text_summary += f"\n[{item.employee_name}] (Arm: {item.locker_number or '?'})\n"
                current_emp = item.employee_name
            text_summary += f" - {item.item_code}: {item.item_description}\n"
            
        return text_summary, items

    def get_employee_info(self, name: str) -> Optional[Tuple[str, str]]:
        """
        Retrieves employee info (Locker, ID/Matricola) from the database by name.
        """
        return self.db.get_employee_by_name(name)

    def register_new_employee(self, id_noleggio: str, name: str, locker: str):
        """
        Registers or updates an employee in the database.
        """
        self.db.upsert_employee(id_noleggio, name, locker)

    def get_all_employees_as_dataframe(self) -> pd.DataFrame:
        """
        Returns all employees as a Pandas DataFrame for the editor.
        """
        return self.db.get_all_employees_df()

    def save_employees_from_dataframe(self, df: pd.DataFrame):
        """
        Saves the modified DataFrame back to the database.
        """
        self.db.save_employees_from_df(df)
