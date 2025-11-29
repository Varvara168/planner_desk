from PyQt6.QtWidgets import (QDialog, QMessageBox, QInputDialog, QListWidgetItem, 
                             QAbstractItemView, QMenu, QInputDialog, QCheckBox, 
                             QHBoxLayout, QWidget, QPushButton, QVBoxLayout, QLabel,
                             QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6 import QtGui
from ui.taskdialog import Ui_Dialog
from db import (add_task, get_tasks_by_date, remove_task, toggle_task_status, 
                update_task, add_mandatory_task_template, get_mandatory_task_templates, 
                remove_mandatory_task_template, toggle_mandatory_status, get_categories,
                get_task)

class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        self.current_date = QDate.currentDate()
        
        # Настройка списка задач
        self.ui.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Добавляем новые кнопки
        self.setup_enhanced_ui()
        
        # Загружаем категории
        self.load_categories()
        
        # Подключаем кнопки
        self.ui.pushButton_2.clicked.connect(self.delete_task)
        self.ui.pushButton.clicked.connect(self.show_enhanced_add_task_dialog)
        self.ui.pushButton_3.clicked.connect(self.close_dialog)
        
        # Двойной клик по задаче для отметки выполнения
        self.ui.listWidget.doubleClicked.connect(self.toggle_task_done)
        
        # Контекстное меню для редактирования
        self.ui.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_context_menu)
        
    def setup_enhanced_ui(self):
        """Настройка улучшенного интерфейса"""
        # Создаем layout для дополнительных кнопок
        additional_buttons_layout = QHBoxLayout()
        
        # Кнопка категорий
        self.categories_btn = QPushButton("📂 Категории")
        self.categories_btn.clicked.connect(self.show_categories_dialog)
        
        # Кнопка экспорта
        self.export_btn = QPushButton("📤 Экспорт")
        self.export_btn.clicked.connect(self.show_export_dialog)
        
        # Кнопка статистики
        self.stats_btn = QPushButton("📊 Статистика")
        self.stats_btn.clicked.connect(self.show_stats)
        
        additional_buttons_layout.addWidget(self.categories_btn)
        additional_buttons_layout.addWidget(self.export_btn)
        additional_buttons_layout.addWidget(self.stats_btn)
        additional_buttons_layout.addStretch()
        
        # Добавляем layout в основной интерфейс
        if hasattr(self.ui, 'verticalLayout'):
            self.ui.verticalLayout.insertLayout(1, additional_buttons_layout)
        
    def load_categories(self):
        """Загрузка категорий для комбобокса"""
        self.categories = get_categories()
        
    def set_date(self, date):
        """Установка даты и загрузка задач"""
        self.current_date = date
        self.setWindowTitle(f"Задачи на {date.toString('dd.MM.yyyy')}")
        self.load_tasks()
        
    def load_tasks(self):
        """Загрузка задач для текущей даты"""
        self.ui.listWidget.clear()
        tasks = get_tasks_by_date(self.current_date)
        
        for task in tasks:
            item = QListWidgetItem()
            
            # Форматируем текст задачи
            status = "✅" if task['done'] else "❌"
            mandatory_indicator = "🔸 " if task['is_mandatory'] else ""
            priority_indicator = "⚡" * task.get('priority', 1)
            category_indicator = f"[{task.get('category_name', '')}] " if task.get('category_name') else ""
            
            task_text = f"{mandatory_indicator}{priority_indicator} {category_indicator}{task['title']} | {status}"
            
            item.setText(task_text)
            item.setData(Qt.ItemDataRole.UserRole, task['id'])
            
            # Настраиваем стиль
            self.style_task_item(item, task)
            
            self.ui.listWidget.addItem(item)
    
    def style_task_item(self, item, task):
        """Стилизация элемента задачи"""
        is_mandatory = task.get('is_mandatory', False)
        is_done = task.get('done', False)
        priority = task.get('priority', 1)
        category_color = task.get('category_color')
        
        # Базовые стили
        if is_mandatory:
            item.setBackground(QtGui.QColor(240, 240, 240))
        
        if is_done:
            font = item.font()
            font.setStrikeOut(True)
            item.setFont(font)
            item.setForeground(QtGui.QColor(150, 150, 150))
        else:
            # Цвет в зависимости от приоритета
            if priority == 3:  # Высокий
                item.setForeground(QtGui.QColor(220, 20, 60))  # Красный
            elif priority == 2:  # Средний
                item.setForeground(QtGui.QColor(255, 140, 0))  # Оранжевый
            else:  # Низкий
                item.setForeground(QtGui.QColor(0, 0, 0))  # Черный
            
            # Цвет категории если есть
            if category_color:
                item.setForeground(QtGui.QColor(category_color))
    
    def show_enhanced_add_task_dialog(self):
        """Показ улучшенного диалога добавления задачи"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить задачу")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Название задачи
        layout.addWidget(QLabel("Название задачи:*"))
        title_input = QTextEdit()
        title_input.setMaximumHeight(60)
        title_input.setPlaceholderText("Введите название задачи...")
        layout.addWidget(title_input)
        
        # Описание
        layout.addWidget(QLabel("Описание:"))
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(80)
        desc_input.setPlaceholderText("Дополнительное описание...")
        layout.addWidget(desc_input)
        
        # Настройки задачи
        settings_layout = QHBoxLayout()
        
        # Категория
        settings_layout.addWidget(QLabel("Категория:"))
        category_combo = QComboBox()
        category_combo.addItem("Без категории", None)
        for category in self.categories:
            category_combo.addItem(category['name'], category['id'])
        settings_layout.addWidget(category_combo)
        
        # Приоритет
        settings_layout.addWidget(QLabel("Приоритет:"))
        priority_combo = QComboBox()
        priority_combo.addItem("🔴 Высокий", 3)
        priority_combo.addItem("🟡 Средний", 2)
        priority_combo.addItem("🟢 Низкий", 1)
        settings_layout.addWidget(priority_combo)
        
        layout.addLayout(settings_layout)
        
        # Чекбоксы
        mandatory_checkbox = QCheckBox("🔸 Обязательная задача")
        layout.addWidget(mandatory_checkbox)
        
        # Кнопки
        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить")
        cancel_button = QPushButton("Отмена")
        
        add_button.clicked.connect(lambda: self.add_enhanced_task(
            dialog, title_input.toPlainText(), desc_input.toPlainText(),
            category_combo.currentData(), priority_combo.currentData(),
            mandatory_checkbox.isChecked()
        ))
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def add_enhanced_task(self, dialog, title, description, category_id, priority, is_mandatory):
        """Добавление задачи с расширенными параметрами"""
        if not title.strip():
            QMessageBox.warning(self, 'Ошибка', 'Введите название задачи')
            return
        
        task_id = add_task(
            title=title.strip(),
            deadline=self.current_date.toString('yyyy-MM-dd'),
            description=description.strip(),
            category_id=category_id,
            priority=priority,
            is_mandatory=is_mandatory
        )
        
        if task_id:
            dialog.accept()
            self.load_tasks()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось добавить задачу')
    
    def show_context_menu(self, position):
        """Показ контекстного меню для редактирования"""
        item = self.ui.listWidget.itemAt(position)
        if not item:
            return
            
        task_id = item.data(Qt.ItemDataRole.UserRole)
        task_info = get_task(task_id)
        
        if not task_info:
            return
            
        menu = QMenu(self)
        
        # Основные действия
        edit_action = menu.addAction("✏️ Редактировать")
        delete_action = menu.addAction("🗑️ Удалить")
        menu.addSeparator()
        
        # Действия с статусом
        if task_info['is_mandatory']:
            toggle_mandatory_action = menu.addAction("📝 Сделать обычной")
        else:
            toggle_mandatory_action = menu.addAction("🔸 Сделать обязательной")
        
        toggle_done_action = menu.addAction("✅ Отметить выполненной" if not task_info['done'] else "❌ Снять отметку")
        menu.addSeparator()
        
        # Действия с приоритетом
        priority_menu = menu.addMenu("⚡ Приоритет")
        high_priority_action = priority_menu.addAction("🔴 Высокий")
        medium_priority_action = priority_menu.addAction("🟡 Средний")
        low_priority_action = priority_menu.addAction("🟢 Низкий")
        
        action = menu.exec(self.ui.listWidget.mapToGlobal(position))
        
        if action == edit_action:
            self.edit_enhanced_task(task_info, item)
        elif action == delete_action:
            self.delete_specific_task(item)
        elif action == toggle_mandatory_action:
            self.toggle_mandatory_status(task_info, item)
        elif action == toggle_done_action:
            self.toggle_specific_task(item)
        elif action == high_priority_action:
            self.change_priority(task_id, 3)
        elif action == medium_priority_action:
            self.change_priority(task_id, 2)
        elif action == low_priority_action:
            self.change_priority(task_id, 1)
    
    def edit_enhanced_task(self, task_info, item):
        """Редактирование задачи с расширенными параметрами"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать задачу")
        dialog.setModal(True)
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Название задачи
        layout.addWidget(QLabel("Название задачи:*"))
        title_input = QTextEdit()
        title_input.setPlainText(task_info['title'])
        title_input.setMaximumHeight(60)
        layout.addWidget(title_input)
        
        # Описание
        layout.addWidget(QLabel("Описание:"))
        desc_input = QTextEdit()
        desc_input.setPlainText(task_info.get('description', ''))
        desc_input.setMaximumHeight(80)
        layout.addWidget(desc_input)
        
        # Настройки
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("Категория:"))
        category_combo = QComboBox()
        category_combo.addItem("Без категории", None)
        for category in self.categories:
            category_combo.addItem(category['name'], category['id'])
            if category['id'] == task_info.get('category_id'):
                category_combo.setCurrentText(category['name'])
        settings_layout.addWidget(category_combo)
        
        settings_layout.addWidget(QLabel("Приоритет:"))
        priority_combo = QComboBox()
        priority_combo.addItem("🔴 Высокий", 3)
        priority_combo.addItem("🟡 Средний", 2)
        priority_combo.addItem("🟢 Низкий", 1)
        priority_combo.setCurrentIndex(3 - task_info.get('priority', 1))
        settings_layout.addWidget(priority_combo)
        
        layout.addLayout(settings_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        
        save_button.clicked.connect(lambda: self.update_enhanced_task(
            dialog, task_info['id'], title_input.toPlainText(),
            desc_input.toPlainText(), category_combo.currentData(),
            priority_combo.currentData()
        ))
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def update_enhanced_task(self, dialog, task_id, title, description, category_id, priority):
        """Обновление задачи с расширенными параметрами"""
        if not title.strip():
            QMessageBox.warning(self, 'Ошибка', 'Введите название задачи')
            return
        
        if update_task(
            task_id=task_id,
            title=title.strip(),
            description=description.strip(),
            category_id=category_id,
            priority=priority
        ):
            dialog.accept()
            self.load_tasks()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось обновить задачу')
    
    def change_priority(self, task_id, priority):
        """Изменение приоритета задачи"""
        if update_task(task_id=task_id, priority=priority):
            self.load_tasks()
    
    def show_categories_dialog(self):
        """Показ диалога управления категориями"""
        from CategoryDialog import CategoryDialog
        dialog = CategoryDialog(self)
        dialog.exec()
        # Обновляем список категорий после закрытия диалога
        self.load_categories()
    
    def show_export_dialog(self):
        """Показ диалога экспорта/импорта"""
        from ExportDialog import ExportDialog
        dialog = ExportDialog(self)
        dialog.exec()
    
    def show_stats(self):
        """Показ статистики"""
        from db import get_task_stats
        stats = get_task_stats()
        
        stats_text = f"""
📊 Статистика задач:

• Всего задач: {stats['total']}
• Выполнено: {stats['completed']}
• На сегодня: {stats['today']}
• Просрочено: {stats['overdue']}
• Процент выполнения: {stats['completion_rate']:.1f}%

Приоритеты:
• Высокий: {stats['priority_stats'].get(3, 0)}
• Средний: {stats['priority_stats'].get(2, 0)}
• Низкий: {stats['priority_stats'].get(1, 0)}
        """
        
        QMessageBox.information(self, 'Статистика', stats_text.strip())
    
    # Остальные методы остаются аналогичными, но с учетом новых возможностей
    def delete_task(self):
        """Удаление выбранной задачи"""
        current_item = self.ui.listWidget.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'Ошибка', 'Выберите задачу для удаления')
            return
            
        self.delete_specific_task(current_item)
    
    def delete_specific_task(self, item):
        """Удаление конкретной задачи"""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, 
            'Подтверждение удаления',
            'Вы уверены, что хотите удалить эту задачу?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            remove_task(task_id)
            self.load_tasks()
    
    def toggle_task_done(self, index):
        """Отметка задачи как выполненной/невыполненной"""
        item = self.ui.listWidget.item(index.row())
        task_id = item.data(Qt.ItemDataRole.UserRole)
        toggle_task_status(task_id)
        self.load_tasks()
    
    def toggle_specific_task(self, item):
        """Изменение статуса задачи через контекстное меню"""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        toggle_task_status(task_id)
        self.load_tasks()
    
    def toggle_mandatory_status(self, task_info, item):
        """Переключение статуса обязательности задачи"""
        from db import toggle_mandatory_status
        new_status = toggle_mandatory_status(task_info['id'])
        if new_status is not False:
            self.load_tasks()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось изменить статус задачи')
    
    def close_dialog(self):
        """Закрытие диалога"""
        self.close()
        
    def show(self):
        """Переопределяем show для обновления задач при каждом открытии"""
        self.load_tasks()
        super().show()