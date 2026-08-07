import sqlite3
import os

# 数据库文件保存路径
DB_FILE = os.getenv("DB_FILE", "rebar_data.db")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rebar_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        drawing_id TEXT NOT NULL,
        component_type TEXT NOT NULL,
        specification TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        weight_kg REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()