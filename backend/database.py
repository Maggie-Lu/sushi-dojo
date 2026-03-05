import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    def get_db():
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

    def init_db():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_name TEXT NOT NULL,
                order_type TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                items TEXT NOT NULL,
                total REAL NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'pending',
                eta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Add eta column if it doesn't exist (for existing deployments)
        cursor.execute("""
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS eta TEXT
        """)
        db.commit()
        cursor.close()
        db.close()
else:
    DB_PATH = "sushi_dojo.db"

    def get_db():
        return sqlite3.connect(DB_PATH)

    def init_db():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                order_type TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                items TEXT NOT NULL,
                total REAL NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'pending',
                eta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        db.close()
