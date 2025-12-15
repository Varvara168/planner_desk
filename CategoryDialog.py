from PyQt6.QtWidgets import (QDialog, QMessageBox, QInputDialog, QListWidgetItem, QColorDialog, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6 import QtGui
from ui.category_dialog import Ui_CategoryDialog
from db import get_categories, add_category, update_category, delete_category

class CategoryDialog(QDialog):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.ui = Ui_CategoryDialog()
        self.ui.setupUi(self)
        self.user_id = user_id
             
        self.selected_color = "#007acc"
        
        # Подключаем кнопки
        self.ui.addCategoryBtn.clicked.connect(self.add_category)
        self.ui.colorButton.clicked.connect(self.choose_color)
        self.ui.editCategoryBtn.clicked.connect(self.edit_category)
        self.ui.deleteCategoryBtn.clicked.connect(self.delete_category)
        self.ui.closeCategoryBtn.clicked.connect(self.close)
        
        # Загружаем категории
        self.load_categories()
        
    def load_categories(self):
        """Загрузка списка категорий"""
        self.ui.categoriesList.clear()
        categories = get_categories(self.user_id)
        
        for category in categories:
            item = QListWidgetItem()
            item.setText(f"● {category['name']}")
            item.setData(Qt.ItemDataRole.UserRole, category)
            
            # Устанавливаем цвет
            color = QtGui.QColor(category['color'])
            item.setForeground(color)
            
            self.ui.categoriesList.addItem(item)
    
    def choose_color(self):
        """Выбор цвета для категории"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.ui.colorButton.setStyleSheet(f"background-color: {self.selected_color};")
    
    def add_category(self):
        """Добавление новой категории"""
        name = self.ui.categoryNameInput.text().strip()
        if not name:
            QMessageBox.warning(self, 'Ошибка', 'Введите название категории')
            return
        
        category_id = add_category(name, self.selected_color)
        if category_id:
            self.ui.categoryNameInput.clear()
            self.load_categories()
            QMessageBox.information(self, 'Успех', 'Категория добавлена')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось добавить категорию')
    
    def edit_category(self):
        """Редактирование выбранной категории"""
        current_item = self.ui.categoriesList.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'Ошибка', 'Выберите категорию для редактирования')
            return
        
        category = current_item.data(Qt.ItemDataRole.UserRole)
        
        new_name, ok = QInputDialog.getText(
            self, 
            'Редактировать категорию', 
            'Новое название:',
            text=category['name']
        )
        
        if ok and new_name.strip():
            color = QColorDialog.getColor(QtGui.QColor(category['color']))
            if color.isValid():
                if update_category(category['id'], new_name.strip(), color.name()):
                    self.load_categories()
                    QMessageBox.information(self, 'Успех', 'Категория обновлена')
                else:
                    QMessageBox.warning(self, 'Ошибка', 'Не удалось обновить категорию')
    
    def delete_category(self):
        """Удаление выбранной категории"""
        current_item = self.ui.categoriesList.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'Ошибка', 'Выберите категорию для удаления')
            return
        
        category = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, 
            'Подтверждение удаления',
            f'Вы уверены, что хотите удалить категорию "{category["name"]}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if delete_category(category['id']):
                self.load_categories()
                QMessageBox.information(self, 'Успех', 'Категория удалена')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось удалить категорию')