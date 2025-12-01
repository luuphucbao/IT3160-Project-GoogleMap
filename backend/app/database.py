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
    print(db_path)
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

def create_session_table():
    """
    Tạo bảng 'edges_session' tạm thời cho phiên làm việc hiện tại.
    Bảng này là một bản sao của bảng 'edges' gốc và sẽ được tạo lại mỗi khi
    ứng dụng khởi động để đảm bảo một môi trường làm việc sạch.
    """
    print("Initializing session table 'edges_session'...")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Xóa bảng session cũ nếu tồn tại
        cursor.execute("DROP TABLE IF EXISTS edges_session")

        # 2. Tạo bảng session mới (giữ nguyên toàn bộ schema)
        cursor.execute("""
            CREATE TABLE edges_session (
                node_from INTEGER NOT NULL,
                node_to   INTEGER NOT NULL,
                weight    REAL NOT NULL,
                PRIMARY KEY(node_from, node_to),
                FOREIGN KEY(node_from) REFERENCES nodes(id),
                FOREIGN KEY(node_to)   REFERENCES nodes(id)
            )
        """)
        # 3. Sao chép dữ liệu từ bảng edges
        cursor.execute("INSERT INTO edges_session SELECT * FROM edges")
        # 4. Tạo lại index để tối ưu truy vấn
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_session_from ON edges_session(node_from)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_session_to ON edges_session(node_to)")
        conn.commit()
    print("✓ Session table 'edges_session' created successfully.")


def init_database():
    """Initialize database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                x REAL NOT NULL,
                y REAL NOT NULL
            )
        """)
        
        # Create edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                node_from INTEGER PRIMARY KEY,
                node_to INTEGER PRIMARY KEY,
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