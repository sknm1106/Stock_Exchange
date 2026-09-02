import os
import sqlite3

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "engineering_stock.db")
SCHEMA_PG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_supabase.sql")

def get_database_url():
    """
    Supabase PostgreSQL DATABASE_URL을 탐색합니다.
    1. Streamlit Secrets (st.secrets["DATABASE_URL"])
    2. OS Environment Variable (os.environ["DATABASE_URL"])
    3. Local .streamlit/secrets.toml file directly
    """
    # 1. Streamlit Secrets
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    # 2. OS Environment Variable
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]

    # 3. Direct parse of .streamlit/secrets.toml
    secrets_file = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
    if os.path.exists(secrets_file):
        try:
            import toml
            data = toml.load(secrets_file)
            if "DATABASE_URL" in data:
                return data["DATABASE_URL"]
        except Exception:
            pass

    return None

def is_postgres():
    """현재 환경에서 PostgreSQL (Supabase)을 사용하는지 여부"""
    return bool(PSYCOPG2_AVAILABLE and get_database_url())

def get_db_connection():
    """
    데이터베이스 연결 객체를 반환합니다.
    - DATABASE_URL이 존재하고 psycopg2가 있으면 Supabase (PostgreSQL)에 연결
    - 그 외의 경우 로컬 SQLite에 연결
    """
    db_url = get_database_url()
    if PSYCOPG2_AVAILABLE and db_url:
        try:
            conn = psycopg2.connect(
                db_url,
                connect_timeout=10,
                sslmode="require"
            )
            return conn
        except Exception as e:
            print(f"⚠️ Supabase PostgreSQL 연결 실패, SQLite로 fallback: {e}")
            pass

    # Fallback to SQLite
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """데이터베이스 스키마를 초기화합니다."""
    conn = get_db_connection()
    
    # PostgreSQL 연결인 경우
    if PSYCOPG2_AVAILABLE and hasattr(conn, "closed") and type(conn).__module__.startswith("psycopg2"):
        try:
            cursor = conn.cursor()
            if os.path.exists(SCHEMA_PG_PATH):
                with open(SCHEMA_PG_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                cursor.execute(schema_sql)
                conn.commit()
                print("✅ Supabase PostgreSQL schema initialized.")
            cursor.close()
        except Exception as e:
            conn.rollback()
            print(f"❌ PostgreSQL schema init error: {e}")
            raise
        finally:
            conn.close()
        return

    # SQLite 연결인 경우
    cursor = conn.cursor()
    
    # 1. users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        coin REAL NOT NULL DEFAULT 0.0,
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
        current_price REAL NOT NULL,
        qr_token TEXT UNIQUE
    )
    """)
    
    cursor.execute("PRAGMA table_info(departments)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'qr_token' not in columns:
        cursor.execute("ALTER TABLE departments ADD COLUMN qr_token TEXT")

    # 3. department_checkins & qr_checkins
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS department_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT DEFAULT '2026_EXPO',
        student_id TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        reward_coin REAL DEFAULT 100.0,
        checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        qr_token_id TEXT,
        UNIQUE(event_id, student_id, department_id),
        FOREIGN KEY (student_id) REFERENCES users(student_id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qr_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        qr_event_id TEXT NOT NULL,
        event_name TEXT NOT NULL,
        reward_coin REAL DEFAULT 100.0,
        checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, qr_event_id),
        FOREIGN KEY (student_id) REFERENCES users(student_id)
    )
    """)

    # 4. holdings
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
    
    # 5. transactions
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
    
    # 6. price_history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER NOT NULL,
        price REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)
    
    # 7. price_schedule
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

    # 8. news
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

