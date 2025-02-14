
import os
import sqlite3
import logging

class Database:
    def __init__(self):
        try:
            self.connection = sqlite3.connect('local.db', check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.create_tables()
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise

    def create_tables(self):
        # Create products table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                mrp REAL NOT NULL,
                barcode TEXT,
                unit TEXT,
                category TEXT,
                hsn_code TEXT,
                gst_rate INTEGER DEFAULT 0,
                cess_rate INTEGER DEFAULT 0
            )
        """)
        self.connection.commit()

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            # Convert PostgreSQL placeholder to SQLite
            query = query.replace('%s', '?')
            cursor.execute(query, params or ())
            self.connection.commit()
            try:
                return cursor.fetchall()
            except:
                return []
        finally:
            cursor.close()
