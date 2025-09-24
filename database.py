import sqlite3
import os
from datetime import datetime

def init_db():
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number INTEGER UNIQUE NOT NULL,
            status TEXT DEFAULT 'available',
            price REAL NOT NULL
        )
    ''')
    
    # Sales table (updated with status and restore_date)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            gestionnaire_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'active',
            restore_date TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms (room_id),
            FOREIGN KEY (gestionnaire_id) REFERENCES users (id)
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gestionnaire_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (gestionnaire_id) REFERENCES users (id)
        )
    ''')
    
    # Check if the status column exists in sales table, if not, add it
    try:
        cursor.execute("SELECT status FROM sales LIMIT 1")
    except sqlite3.OperationalError:
        # Add the status column if it doesn't exist
        cursor.execute('ALTER TABLE sales ADD COLUMN status TEXT DEFAULT "active"')
    
    # Check if the restore_date column exists in sales table, if not, add it
    try:
        cursor.execute("SELECT restore_date FROM sales LIMIT 1")
    except sqlite3.OperationalError:
        # Add the restore_date column if it doesn't exist
        cursor.execute('ALTER TABLE sales ADD COLUMN restore_date TEXT')
    
    # Check if admin user exists
    cursor.execute("SELECT * FROM users WHERE name='Crescent'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, role, password) VALUES (?, ?, ?)",
            ('Crescent', 'admin', 'Crescent1#')
        )
    
    # Add a sample gestionnaire user
    cursor.execute("SELECT * FROM users WHERE name='gestionnaire'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, role, password) VALUES (?, ?, ?)",
            ('gestionnaire', 'gestionnaire', 'gest123')
        )
    
    # Add some sample rooms if none exist
    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 51):
            cursor.execute(
                "INSERT INTO rooms (room_number, price) VALUES (?, ?)",
                (i, 50000 if i <= 25 else 75000)  # Different prices for different rooms
            )
    
    # Update existing sales records to have status 'active' if they don't have it
    cursor.execute("UPDATE sales SET status = 'active' WHERE status IS NULL")
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    return conn