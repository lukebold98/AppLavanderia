import sqlite3
import pandas as pd
import os

class DatabaseManager:
    def __init__(self, db_path="Data/AppLavanderia.db"):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Apre la connessione al database."""
        self.conn = sqlite3.connect(self.db_path)
        # Questo comando è fondamentale: attiva il supporto alle Foreign Keys in SQLite
        # Senza questo, i vincoli relazionali verrebbero ignorati!
        self.conn.execute("PRAGMA foreign_keys = ON")
        return self.conn

    def close(self):
        """Chiude la connessione se aperta."""
        if self.conn:
            self.conn.close()

    def create_schema(self):
        """Crea le tabelle necessarie per il nuovo schema relazionale."""
        self.connect()
        cursor = self.conn.cursor()

        # 1. Tabella DIPENDENTI
        # Added 'matricola' as a unique identifier for business logic (Badge ID)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Dipendenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricola TEXT UNIQUE,
            nome TEXT NOT NULL,
            reparto TEXT,
            numero_armadietto TEXT
        )
        ''')

        # 2. Tabella ARTICOLI
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Articoli (
            codice TEXT PRIMARY KEY,
            descrizione TEXT NOT NULL
        )
        ''')

        # 3. Tabella DOTAZIONE (Cosa DEVE avere ognuno)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Dotazione (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dipendente_id INTEGER,
            articolo_codice TEXT,
            quantita_prevista INTEGER DEFAULT 1,
            FOREIGN KEY(dipendente_id) REFERENCES Dipendenti(id),
            FOREIGN KEY(articolo_codice) REFERENCES Articoli(codice)
        )
        ''')

        # 4. Tabella CONSEGNE
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Consegne (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_consegna DATE,
            numero_bolla TEXT
        )
        ''')

        # 5. Tabella RIGHE_CONSEGNA
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS RigheConsegna (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consegna_id INTEGER,
            dipendente_id INTEGER,
            articolo_codice TEXT,
            quantita_ricevuta INTEGER DEFAULT 0,
            FOREIGN KEY(consegna_id) REFERENCES Consegne(id),
            FOREIGN KEY(dipendente_id) REFERENCES Dipendenti(id),
            FOREIGN KEY(articolo_codice) REFERENCES Articoli(codice)
        )
        ''')

        self.conn.commit()
        print("Database e tabelle creati con successo!")
        self.close()

    # --- Methods for Controller (replacing DB_manager.py) ---

    def get_employee_by_name(self, name: str):
        """
        Cerca un dipendente per nome.
        Returns: (armadietto, matricola) or None
        """
        self.connect()
        cursor = self.conn.cursor()
        # Usiamo LIKE per flessibilità
        cursor.execute("SELECT numero_armadietto, matricola FROM Dipendenti WHERE nome LIKE ?", (f"%{name}%",))
        result = cursor.fetchone()
        self.close()
        return result

    def upsert_employee(self, matricola: str, name: str, locker: str):
        """
        Inserisce o aggiorna un dipendente.
        Uses matricola as the unique key for upsert if possible, otherwise checks name.
        """
        self.connect()
        cursor = self.conn.cursor()
        
        # Logic: Try using matricola as unique key.
        try:
            cursor.execute("INSERT INTO Dipendenti (matricola, nome, numero_armadietto) VALUES (?, ?, ?) ON CONFLICT(matricola) DO UPDATE SET nome=excluded.nome, numero_armadietto=excluded.numero_armadietto", 
                           (matricola, name, locker))
            self.conn.commit()
        except sqlite3.OperationalError:
            # Fallback for simple insert or replace if syntax issues (though ON CONFLICT is standard since 3.24)
            cursor.execute("INSERT OR REPLACE INTO Dipendenti (matricola, nome, numero_armadietto) VALUES (?, ?, ?)", 
                           (matricola, name, locker))
            self.conn.commit()
        finally:
            self.close()

    def get_all_employees_df(self) -> pd.DataFrame:
        """Returns all employees as a Pandas DataFrame."""
        self.connect()
        try:
            df = pd.read_sql_query("SELECT * FROM Dipendenti", self.conn)
        except Exception:
            df = pd.DataFrame()
        finally:
            self.close()
        return df

    def save_employees_from_df(self, df: pd.DataFrame):
        """Overwrites the Dipendenti table with the dataframe content."""
        self.connect()
        df.to_sql("Dipendenti", self.conn, if_exists="replace", index=False)
        self.conn.commit()
        self.close()

# Se eseguiamo questo file direttamente, ricrea il DB
if __name__ == "__main__":
    db = DatabaseManager()
    db.create_schema()
