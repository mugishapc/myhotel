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
    
    # Rooms table - updated with separate prices for full and passage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number INTEGER UNIQUE NOT NULL,
            status TEXT DEFAULT 'available',
            price_full REAL NOT NULL,
            price_passage REAL NOT NULL
        )
    ''')
    
    # Sales table - updated with sale_type column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            gestionnaire_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'active',
            restore_date TEXT,
            sale_type TEXT NOT NULL DEFAULT 'full',
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
    
    # Check if old price column exists and migrate data
    cursor.execute("PRAGMA table_info(rooms)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'price' in columns and 'price_full' not in columns:
        # Add the new price columns
        cursor.execute('ALTER TABLE rooms ADD COLUMN price_full REAL NOT NULL DEFAULT 0')
        cursor.execute('ALTER TABLE rooms ADD COLUMN price_passage REAL NOT NULL DEFAULT 0')
        
        # Migrate existing price data
        cursor.execute("SELECT room_id, price FROM rooms")
        rooms = cursor.fetchall()
        for room in rooms:
            cursor.execute(
                "UPDATE rooms SET price_full = ?, price_passage = ? WHERE room_id = ?",
                (room[1], room[1] * 0.6, room[0])  # Passage price is 60% of full price by default
            )
        
        # Remove the old price column (SQLite doesn't support DROP COLUMN directly)
        # Instead, we'll create a new table and copy data
        cursor.execute('''
            CREATE TABLE rooms_new (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number INTEGER UNIQUE NOT NULL,
                status TEXT DEFAULT 'available',
                price_full REAL NOT NULL,
                price_passage REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            INSERT INTO rooms_new (room_id, room_number, status, price_full, price_passage)
            SELECT room_id, room_number, status, price_full, price_passage FROM rooms
        ''')
        
        cursor.execute('DROP TABLE rooms')
        cursor.execute('ALTER TABLE rooms_new RENAME TO rooms')
    
    # Check if sale_type column exists in sales table
    cursor.execute("PRAGMA table_info(sales)")
    sales_columns = [column[1] for column in cursor.fetchall()]
    
    if 'sale_type' not in sales_columns:
        cursor.execute('ALTER TABLE sales ADD COLUMN sale_type TEXT NOT NULL DEFAULT "full"')
    
    if 'status' not in sales_columns:
        cursor.execute('ALTER TABLE sales ADD COLUMN status TEXT DEFAULT "active"')
    
    if 'restore_date' not in sales_columns:
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
            price_full = 50000 if i <= 25 else 75000
            price_passage = price_full * 0.6  # 60% of full price
            cursor.execute(
                "INSERT INTO rooms (room_number, price_full, price_passage) VALUES (?, ?, ?)",
                (i, price_full, price_passage)
            )
    
    # Update existing sales records to have proper defaults
    cursor.execute("UPDATE sales SET status = 'active' WHERE status IS NULL")
    cursor.execute("UPDATE sales SET sale_type = 'full' WHERE sale_type IS NULL")
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    return conn

def verify_user(username, password):
    """Verify user credentials and return user data if valid"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE name = ? AND password = ?',
        (username, password)
    ).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    conn.close()
    return user 