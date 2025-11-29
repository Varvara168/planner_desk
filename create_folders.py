import os

def create_data_folders():
    """Создание папок для данных"""
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

if __name__ == "__main__":
    create_data_folders()