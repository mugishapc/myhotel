import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Use environment variable for security (or fallback to your Render URL)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://myhotel_user:PKPNiLeBWPOeZHEBB93j7NghdgPqXjc9@dpg-d3bf67umcj7s73ernsr0-a.oregon-postgres.render.com/myhotel"
)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Rooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id SERIAL PRIMARY KEY,
            room_number INT UNIQUE NOT NULL,
            status TEXT DEFAULT 'available',
            price_full REAL NOT NULL,
            price_passage REAL NOT NULL
        )
    """)

    # Sales table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            room_id INT NOT NULL REFERENCES rooms(room_id),
            gestionnaire_id INT NOT NULL REFERENCES users(id),
            date DATE NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'active',
            restore_date DATE,
            sale_type TEXT DEFAULT 'full'
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            gestionnaire_id INT NOT NULL REFERENCES users(id),
            reason TEXT NOT NULL,
            amount REAL NOT NULL,
            date DATE NOT NULL
        )
    """)

    # Default admin user
    cursor.execute("SELECT * FROM users WHERE name='Crescent'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, role, password) VALUES (%s, %s, %s)",
            ('Crescent', 'admin', 'Crescent12#')
        )

    # Sample gestionnaire
    cursor.execute("SELECT * FROM users WHERE name='gestionnaire'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, role, password) VALUES (%s, %s, %s)",
            ('gestionnaire', 'gestionnaire', 'gest123')
        )

    # Sample rooms if empty
    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()['count'] == 0:
        for i in range(1, 51):
            price_full = 50000 if i <= 25 else 75000
            price_passage = price_full * 0.6
            cursor.execute(
                "INSERT INTO rooms (room_number, price_full, price_passage) VALUES (%s, %s, %s)",
                (i, price_full, price_passage)
            )

    conn.commit()
    cursor.close()
    conn.close()
