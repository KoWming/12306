import sqlite3
import os

# Database file path
DB_FILE = "./data/12306.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 1. Create system_configs table
        print("Creating system_configs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(50) UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Add allow_scheduled_start column to tasks table
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "allow_scheduled_start" in columns:
            print("Column 'allow_scheduled_start' already exists.")
        else:
            print("Adding 'allow_scheduled_start' column to tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN allow_scheduled_start BOOLEAN DEFAULT 1")
        
        conn.commit()
        print("Migration successful!")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
