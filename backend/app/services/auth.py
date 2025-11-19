from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings
from app.database import get_db_connection

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> dict | None:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        token_type = payload.get("type")
        if token_type != expected_type:
            return None
        
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None:
            return None
        
        return {"username": username, "role": role}
    
    except JWTError:
        return None


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate user against database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, hashed_password, role FROM admin WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return None
        
        if not verify_password(password, user["hashed_password"]):
            return None
        
        return {
            "username": user["username"],
            "role": user["role"]
        }


def create_admin_user(username: str, password: str, role: str = "admin"):
    """Create a new admin user"""
    hashed_password = get_password_hash(password)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO admin (username, hashed_password, role) VALUES (?, ?, ?)",
                (username, hashed_password, role)
            )
            return True
        except sqlite3.IntegrityError:
            # User already exists
            return False