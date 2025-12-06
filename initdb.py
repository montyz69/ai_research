import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import init_db, engine
from app.core.logger import setup_logger
from sqlalchemy import text

logger = setup_logger(__name__)

def check_database_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection successful")
        logger.info("Database connection established")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        logger.error(f"Database connection error: {str(e)}")
        return False

def initialize_database():
    print("=" * 60)
    print("AI Research Framework - Database Initialization")
    print("=" * 60)
    
    print("\n1. Checking database connection...")
    if not check_database_connection():
        print("\nPlease ensure:")
        print("  - PostgreSQL is running")
        print("  - Database exists (createdb ai_research_db)")
        print("  - DATABASE_URL in .env is correct")
        return False
    
    print("\n2. Creating database tables...")
    try:
        init_db()
        print("✓ Database tables created successfully")
        logger.info("Database initialized successfully")
        
        print("\n3. Verifying tables...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            if tables:
                print(f"✓ Created {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("✗ No tables found")
                return False
        
        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Database initialization failed: {str(e)}")
        logger.error(f"Database initialization error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    try:
        result = initialize_database()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)