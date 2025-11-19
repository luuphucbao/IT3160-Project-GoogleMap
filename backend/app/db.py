import sqlite3
from contextlib import contextmanager
from pathlib import Path
from app.config import get_settings

settings = get_settings()


def get_db_path() -> str:
    """Get database file path from settings"""
    # Extract path from SQLite URL (remove 'sqlite:///')
    db_path = settings.database_url.replace("sqlite:///", "")
    
    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    return db_path


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                x REAL NOT NULL,
                y REAL NOT NULL
            )
        """)
        
        # Create edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_from INTEGER NOT NULL,
                node_to INTEGER NOT NULL,
                weight REAL NOT NULL,
                FOREIGN KEY (node_from) REFERENCES nodes(id),
                FOREIGN KEY (node_to) REFERENCES nodes(id)
            )
        """)
        
        # Create index on edges for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_from 
            ON edges(node_from)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_to 
            ON edges(node_to)
        """)
        
        # Create admin table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin'
            )
        """)
        
        conn.commit()
        print("✓ Database tables created successfully")