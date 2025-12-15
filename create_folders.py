import os
import sqlite3

def create_data_folders():
    """Создание папок для данных и пустой базы"""
    folders = [
        'data',
        'data/backups',
        'data/exports', 
        'data/templates',
        'data/logs'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Создана папка: {folder}")
    
    db_path = os.path.join('data', 'planner.db')
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                task_date TEXT,
                description TEXT,
                priority INTEGER DEFAULT 1,
                is_mandatory INTEGER DEFAULT 0,
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("Создана пустая база данных planner.db")
    else:
        print("База данных уже существует")

if __name__ == "__main__":
    create_data_folders()
