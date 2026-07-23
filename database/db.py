import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "engineering_stock.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        coin REAL NOT NULL DEFAULT 100.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. departments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        code TEXT,
        description TEXT,
        current_price REAL NOT NULL
    )
    """)
    
    # 3. holdings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holdings (
        student_id TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        average_price REAL NOT NULL DEFAULT 0.0,
        PRIMARY KEY (student_id, department_id),
        FOREIGN KEY (student_id) REFERENCES users(student_id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)
    
    # 4. transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(student_id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)
    
    # 5. price_history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER NOT NULL,
        price REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)
    
    # 6. price_schedule
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER NOT NULL,
        scheduled_time DATETIME NOT NULL,
        price REAL NOT NULL,
        is_applied INTEGER DEFAULT 0,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)

    # 7. news
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        impact TEXT DEFAULT 'NEUTRAL',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)
    
    conn.commit()
    conn.close()
