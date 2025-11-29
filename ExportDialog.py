from PyQt6.QtWidgets import (QDialog, QMessageBox, QFileDialog, QInputDialog)
from PyQt6.QtCore import QDate
from ui.export_dialog import Ui_ExportDialog
from db import (export_tasks_to_json, import_tasks_from_json, 
                save_template, get_available_templates, get_tasks_by_date)

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ExportDialog()
        self.ui.setupUi(self)
        
        self.selected_file = None
        
        # Подключаем кнопки
        self.ui.exportBtn.clicked.connect(self.export_tasks)
        self.ui.backupBtn.clicked.connect(self.create_backup)
        self.ui.importBtn.clicked.connect(self.import_tasks)
        self.ui.selectFileBtn.clicked.connect(self.select_file)
        self.ui.saveTemplateBtn.clicked.connect(self.save_template)
        self.ui.loadTemplateBtn.clicked.connect(self.load_template)
        self.ui.closeExportBtn.clicked.connect(self.close)
    
    def export_tasks(self):
        """Экспорт задач в JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            'Экспорт задач', 
            f'backup_{QDate.currentDate().toString("yyyyMMdd")}.json',
            'JSON Files (*.json)'
        )
        
        if filename:
            if export_tasks_to_json(filename):
                QMessageBox.information(self, 'Успех', 'Задачи успешно экспортированы')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось экспортировать задачи')
    
    def create_backup(self):
        """Создание автоматического бэкапа"""
        if export_tasks_to_json():
            QMessageBox.information(self, 'Успех', 'Автоматический бэкап создан')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось создать бэкап')
    
    def select_file(self):
        """Выбор файла для импорта"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            'Выберите файл для импорта', 
            '', 
            'JSON Files (*.json)'
        )
        
        if filename:
            self.selected_file = filename
            self.ui.selectedFileLabel.setText(f"Выбран: {filename.split('/')[-1]}")
    
    def import_tasks(self):
        """Импорт задач из JSON"""
        if not self.selected_file:
            QMessageBox.warning(self, 'Ошибка', 'Сначала выберите файл')
            return
        
        reply = QMessageBox.question(
            self, 
            'Подтверждение импорта',
            'Вы уверены, что хотите импортировать задачи? Существующие задачи не будут удалены.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if import_tasks_from_json(self.selected_file):
                QMessageBox.information(self, 'Успех', 'Задачи успешно импортированы')
                self.selected_file = None
                self.ui.selectedFileLabel.setText("Файл не выбран")
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось импортировать задачи')
    
    def save_template(self):
        """Сохранение шаблона задач"""
        template_name, ok = QInputDialog.getText(
            self, 
            'Сохранение шаблона', 
            'Введите название шаблона:'
        )
        
        if ok and template_name.strip():
            # Получаем задачи на сегодня для шаблона
            today_tasks = get_tasks_by_date(QDate.currentDate())
            template_data = []
            
            for task in today_tasks:
                template_data.append({
                    'title': task['title'],
                    'is_mandatory': task['is_mandatory'],
                    'priority': task['priority'],
                    'category_id': task['category_id']
                })
            
            if save_template(template_name.strip(), template_data):
                QMessageBox.information(self, 'Успех', 'Шаблон сохранен')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось сохранить шаблон')
    
    def load_template(self):
        """Загрузка шаблона задач"""
        templates = get_available_templates()
        if not templates:
            QMessageBox.information(self, 'Информация', 'Нет доступных шаблонов')
            return
        
        template_name, ok = QInputDialog.getItem(
            self, 
            'Загрузка шаблона', 
            'Выберите шаблон:',
            templates, 
            0, 
            False
        )
        
        if ok and template_name:
            # Здесь можно добавить логику применения шаблона
            QMessageBox.information(self, 'Успех', f'Шаблон "{template_name}" загружен')