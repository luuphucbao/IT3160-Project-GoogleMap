"""
Database initialization script
Creates tables and default admin user
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database import init_database
from app.services.auth import create_admin_user
from app.config import get_settings


def main():
    """Initialize database and create default admin"""
    print("=== Initializing PathFinding Database ===\n")
    
    # Initialize tables
    print("Creating database tables...")
    init_database()
    
    # Create default admin user
    settings = get_settings()
    print(f"\nCreating default admin user: {settings.default_admin_username}")
    
    success = create_admin_user(
        username=settings.default_admin_username,
        password=settings.default_admin_password,
        role="admin"
    )
    
    if success:
        print(f"✓ Admin user created successfully")
        print(f"  Username: {settings.default_admin_username}")
        print(f"  Password: {settings.default_admin_password}")
        print(f"\n⚠️  IMPORTANT: Change the default password in production!")
    else:
        print(f"✓ Admin user already exists")
    
    print("\n=== Database initialization complete ===")


if __name__ == "__main__":
    main()