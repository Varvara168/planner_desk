from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QCheckBox,
                             QPushButton, QMessageBox)
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtCore import QDate
from db import add_task, update_task, get_categories

def create_task_editor_dialog(parent, mode='add', task_data=None, date=None, user_id=1):
    """
    СОЗДАЕТ ВАШ ДИАЛОГ ТОЧНО ТАК ЖЕ как в WeekDialog.py
    """
    dialog = QDialog(parent)
    
    if mode == 'add':
        dialog.setWindowTitle(f"Добавить задачу на {date.toString('dd.MM.yyyy')}")
    else:
        dialog.setWindowTitle("Редактировать задачу")
    
    dialog.setModal(True)
    dialog.resize(400, 400) 
    
    layout = QVBoxLayout(dialog)
    
    title_label = QLabel("Название задачи:")
    title_edit = QLineEdit()
    layout.addWidget(title_label)
    layout.addWidget(title_edit)
    
    desc_label = QLabel("Описание:")
    desc_edit = QTextEdit()
    desc_edit.setMaximumHeight(80)
    layout.addWidget(desc_label)
    layout.addWidget(desc_edit)
    
    priority_label = QLabel("Приоритет:")
    priority_combo = QComboBox()
    priority_combo.addItem("🟢 Низкий", 1)
    priority_combo.addItem("🟡 Средний", 2)
    priority_combo.addItem("🔴 Высокий", 3)
    layout.addWidget(priority_label)
    layout.addWidget(priority_combo)
    
    category_label = QLabel("Категория:")
    category_combo = QComboBox()
    
    categories = get_categories(user_id)

    for category in categories:
        color = category.get('color', '#007acc')
        icon_pixmap = QPixmap(16, 16)
        icon_pixmap.fill(QColor(color))
        icon = QIcon(icon_pixmap)
        category_combo.addItem(icon, category['name'], category['id'])
    
    layout.addWidget(category_label)
    layout.addWidget(category_combo)
    
    mandatory_check = QCheckBox("🔸 Обязательная задача")
    layout.addWidget(mandatory_check)
    
    if mode == 'edit' and task_data:
        title_edit.setText(task_data.get('title', ''))
        desc_edit.setPlainText(task_data.get('description', ''))
        
        # Приоритет
        current_priority = task_data.get('priority', 1)
        index = priority_combo.findData(current_priority)
        if index >= 0:
            priority_combo.setCurrentIndex(index)
        
        # Категория
        current_category_id = task_data.get('category_id')
        if current_category_id:
            # Находим индекс категории
            for i in range(category_combo.count()):
                if category_combo.itemData(i) == current_category_id:
                    category_combo.setCurrentIndex(i)
                    break
        
        # Обязательность
        mandatory_check.setChecked(task_data.get('is_mandatory', False))
    
    button_layout = QHBoxLayout()
    
    if mode == 'add':
        save_btn = QPushButton("➕ Добавить")
    else:
        save_btn = QPushButton("💾 Сохранить")
    
    cancel_btn = QPushButton("❌ Отмена")
    
    button_layout.addWidget(save_btn)
    button_layout.addWidget(cancel_btn)
    layout.addLayout(button_layout)
    
    def save_task():
        title = title_edit.text().strip()
        if not title:
            QMessageBox.warning(dialog, 'Ошибка', 'Введите название задачи')
            return
        
        if mode == 'add':
            result = add_task(
                title=title,
                task_date=date.toString('yyyy-MM-dd'),
                user_id=user_id,
                description=desc_edit.toPlainText(),
                category_id=category_combo.currentData(),
                priority=priority_combo.currentData(),
                is_mandatory=mandatory_check.isChecked()
            )
        else:
            result = update_task(
                user_id=user_id,
                task_id=task_data['id'],
                title=title,
                description=desc_edit.toPlainText(),
                priority=priority_combo.currentData(),
                category_id=category_combo.currentData(),
                is_mandatory=mandatory_check.isChecked()
            )
        
        if result:
            dialog.accept()
        else:
            QMessageBox.warning(dialog, 'Ошибка', 
                               f'Не удалось {"добавить" if mode == "add" else "обновить"} задачу')
    
    save_btn.clicked.connect(save_task)
    cancel_btn.clicked.connect(dialog.reject)
    
    title_edit.setFocus()
    
    return dialog
