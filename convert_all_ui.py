import os
import sys
from PyQt6 import uic

def convert_ui_files():
    """Конвертирует все UI файлы в Python код"""
    ui_files = [
        'ui/main_window.ui',
        'ui/taskdialog.ui',
        'ui/week_dialog.ui', 
        'ui/category_dialog.ui',
        'ui/export_dialog.ui',
        'ui/autorisation.ui'
    ]
    
    for ui_file in ui_files:
        if os.path.exists(ui_file):
            py_file = ui_file.replace('.ui', '.py')
            try:
                print(f"Конвертирую {ui_file} -> {py_file}")
                
                with open(ui_file, 'r', encoding='utf-8') as f:
                    with open(py_file, 'w', encoding='utf-8') as out:
                        uic.compileUi(f, out)
                
                print(f"✓ Успешно: {py_file}")
                
            except Exception as e:
                print(f"✗ Ошибка при конвертации {ui_file}: {e}")
        else:
            print(f"✗ Файл не найден: {ui_file}")

if __name__ == "__main__":
    print("=== Конвертация UI файлов ===")
    convert_ui_files()
    print("=== Готово! ===")