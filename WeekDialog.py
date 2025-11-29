from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QWidget, QFrame, QPushButton, 
                             QMenu, QInputDialog, QMessageBox, QLineEdit, 
                             QCheckBox, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6 import QtGui
from ui.week_dialog import Ui_WeekDialog
from db import get_tasks_by_week, add_task, update_task, remove_task, toggle_task_status, toggle_mandatory_status

class WeekDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_WeekDialog()
        self.ui.setupUi(self)
        
        self.current_date = QDate.currentDate()
        self.week_layout = self.ui.weekLayout
        
        # Подключаем кнопки навигации
        self.ui.prevWeekBtn.clicked.connect(self.prev_week)
        self.ui.nextWeekBtn.clicked.connect(self.next_week)
        self.ui.closeBtn.clicked.connect(self.close_dialog)
        
        self.load_week_tasks()
        
    def load_week_tasks(self):
        """Загрузка и отображение задач на неделю"""
        self.clear_week_layout()
        
        self.tasks_by_day = get_tasks_by_week(self.current_date)
        
        # Обновляем заголовок
        end_date = self.current_date.addDays(6)
        self.ui.weekLabel.setText(
            f"Неделя: {self.current_date.toString('dd.MM.yyyy')} - {end_date.toString('dd.MM.yyyy')}"
        )
        
        # Дни недели на русском
        days_russian = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        
        # Создаем виджеты для каждого дня недели
        for i in range(7):
            current_date = self.current_date.addDays(i)
            date_str = current_date.toString('yyyy-MM-dd')
            
            day_frame = self.create_day_frame(days_russian[i], current_date, date_str)
            self.week_layout.addWidget(day_frame)
    
    def clear_week_layout(self):
        """Очистка layout недели"""
        while self.week_layout.count():
            item = self.week_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def create_day_frame(self, day_name, current_date, date_str):
        """Создание фрейма для дня"""
        day_frame = QFrame()
        day_frame.setFrameStyle(QFrame.Shape.Box)
        day_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin: 5px;
                padding: 10px;
            }
        """)
        
        day_layout = QVBoxLayout(day_frame)
        
        # Заголовок дня
        header_layout = QHBoxLayout()
        day_title = QLabel(f"{day_name} ({current_date.toString('dd.MM.yyyy')})")
        day_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #2c3e50;")
        
        add_day_task_btn = QPushButton("+")
        add_day_task_btn.setFixedSize(25, 25)
        add_day_task_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_day_task_btn.clicked.connect(lambda checked, date=current_date: self.add_task_to_day(date))
        
        header_layout.addWidget(day_title)
        header_layout.addStretch()
        header_layout.addWidget(add_day_task_btn)
        day_layout.addLayout(header_layout)
        
        # Задачи для этого дня
        day_tasks = self.tasks_by_day.get(date_str, [])
        
        if day_tasks:
            for task in day_tasks:
                task_widget = self.create_task_widget(task, current_date)
                day_layout.addWidget(task_widget)
        else:
            no_tasks_label = QLabel("Нет задач")
            no_tasks_label.setStyleSheet("color: #6c757d; font-style: italic;")
            day_layout.addWidget(no_tasks_label)
        
        day_layout.addStretch()
        return day_frame
    
    def create_task_widget(self, task, date):
        """Создание виджета для одной задачи"""
        task_frame = QFrame()
        
        is_mandatory = task.get('is_mandatory', False)
        is_done = task.get('done', False)
        priority = task.get('priority', 1)
        
        # Стили в зависимости от типа задачи и приоритета
        if is_done:
            # Выполненные задачи
            task_frame.setStyleSheet("""
                QFrame {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 3px;
                    margin: 2px;
                    padding: 5px;
                }
            """)
        elif is_mandatory:
            # Обязательные задачи
            task_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 3px;
                    margin: 2px;
                    padding: 5px;
                }
            """)
        else:
            # Обычные задачи с цветом по приоритету
            if priority == 3:  # Высокий
                task_frame.setStyleSheet("""
                    QFrame {
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 3px;
                        margin: 2px;
                        padding: 5px;
                    }
                """)
            elif priority == 2:  # Средний
                task_frame.setStyleSheet("""
                    QFrame {
                        background-color: #d1ecf1;
                        border: 1px solid #bee5eb;
                        border-radius: 3px;
                        margin: 2px;
                        padding: 5px;
                    }
                """)
            else:  # Низкий
                task_frame.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #e9ecef;
                        border-radius: 3px;
                        margin: 2px;
                        padding: 5px;
                    }
                """)
        
        task_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        task_frame.customContextMenuRequested.connect(
            lambda pos, t=task, d=date: self.show_task_context_menu(pos, t, d)
        )
        
        task_layout = QHBoxLayout(task_frame)
        
        # Статус задачи
        status = "✅" if is_done else "⏳"
        status_label = QLabel(status)
        
        # Текст задачи
        task_text = QLabel(task.get('title', 'Без названия'))
        if is_done:
            task_text.setStyleSheet("text-decoration: line-through; color: gray;")
        
        # Иконка приоритета
        priority_icon = QLabel()
        if priority == 3:
            priority_icon.setText("🔴")
        elif priority == 2:
            priority_icon.setText("🟡")
        else:
            priority_icon.setText("🟢")
        
        task_layout.addWidget(status_label)
        task_layout.addWidget(priority_icon)
        task_layout.addWidget(task_text)
        task_layout.addStretch()
        
        return task_frame
    
    def show_task_context_menu(self, position, task, date):
        """Контекстное меню для задачи"""
        menu = QMenu(self)
        
        edit_action = menu.addAction("✏️ Редактировать")
        delete_action = menu.addAction("🗑️ Удалить")
        menu.addSeparator()
        
        is_mandatory = task.get('is_mandatory', False)
        if is_mandatory:
            toggle_mandatory_action = menu.addAction("📝 Сделать обычной")
        else:
            toggle_mandatory_action = menu.addAction("🔸 Сделать обязательной")
        
        is_done = task.get('done', False)
        toggle_action = menu.addAction("✅ Отметить выполненной" if not is_done else "❌ Снять отметку")
        
        menu.addSeparator()
        priority_menu = menu.addMenu("🎯 Приоритет")
        high_priority = priority_menu.addAction("🔴 Высокий")
        medium_priority = priority_menu.addAction("🟡 Средний")
        low_priority = priority_menu.addAction("🟢 Низкий")
        
        action = menu.exec(self.mapToGlobal(position))
        
        if action == edit_action:
            self.edit_task(task)
        elif action == delete_action:
            self.delete_task(task)
        elif action == toggle_mandatory_action:
            self.toggle_mandatory_status(task)
        elif action == toggle_action:
            self.toggle_task(task)
        elif action == high_priority:
            self.set_task_priority(task, 3)
        elif action == medium_priority:
            self.set_task_priority(task, 2)
        elif action == low_priority:
            self.set_task_priority(task, 1)
    
    def edit_task(self, task):
        """Редактирование задачи"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать задачу")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Поле для названия
        title_label = QLabel("Название задачи:")
        title_edit = QLineEdit()
        title_edit.setText(task.get('title', ''))
        layout.addWidget(title_label)
        layout.addWidget(title_edit)
        
        # Поле для описания
        desc_label = QLabel("Описание:")
        desc_edit = QTextEdit()
        desc_edit.setPlainText(task.get('description', ''))
        desc_edit.setMaximumHeight(100)
        layout.addWidget(desc_label)
        layout.addWidget(desc_edit)
        
        # Приоритет
        priority_label = QLabel("Приоритет:")
        priority_combo = QComboBox()
        priority_combo.addItem("🟢 Низкий", 1)
        priority_combo.addItem("🟡 Средний", 2)
        priority_combo.addItem("🔴 Высокий", 3)
        
        # Устанавливаем текущий приоритет
        current_priority = task.get('priority', 1)
        index = priority_combo.findData(current_priority)
        if index >= 0:
            priority_combo.setCurrentIndex(index)
        
        layout.addWidget(priority_label)
        layout.addWidget(priority_combo)
        
        # Чекбокс обязательности
        mandatory_check = QCheckBox("Обязательная задача")
        mandatory_check.setChecked(task.get('is_mandatory', False))
        layout.addWidget(mandatory_check)
        
        # Кнопки
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        def save_task():
            new_title = title_edit.text().strip()
            if not new_title:
                QMessageBox.warning(self, 'Ошибка', 'Введите название задачи')
                return
            
            update_task(
                task['id'],
                title=new_title,
                description=desc_edit.toPlainText(),
                priority=priority_combo.currentData(),
                is_mandatory=mandatory_check.isChecked()
            )
            dialog.accept()
            self.load_week_tasks()
        
        save_btn.clicked.connect(save_task)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def delete_task(self, task):
        """Удаление задачи"""
        reply = QMessageBox.question(
            self, 
            'Подтверждение удаления',
            'Вы уверены, что хотите удалить эту задачу?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            remove_task(task['id'])
            self.load_week_tasks()
    
    def toggle_task(self, task):
        """Изменение статуса задачи"""
        toggle_task_status(task['id'])
        self.load_week_tasks()
    
    def toggle_mandatory_status(self, task):
        """Переключение статуса обязательности"""
        toggle_mandatory_status(task['id'])
        self.load_week_tasks()
    
    def set_task_priority(self, task, priority):
        """Установка приоритета задачи"""
        update_task(task['id'], priority=priority)
        self.load_week_tasks()
    
    def add_task_to_day(self, date):
        """Добавление задачи на день"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Добавить задачу на {date.toString('dd.MM.yyyy')}")
        dialog.setModal(True)
        dialog.resize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        # Поле для названия
        title_label = QLabel("Название задачи:")
        title_edit = QLineEdit()
        layout.addWidget(title_label)
        layout.addWidget(title_edit)
        
        # Поле для описания
        desc_label = QLabel("Описание:")
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(80)
        layout.addWidget(desc_label)
        layout.addWidget(desc_edit)
        
        # Приоритет
        priority_label = QLabel("Приоритет:")
        priority_combo = QComboBox()
        priority_combo.addItem("🟢 Низкий", 1)
        priority_combo.addItem("🟡 Средний", 2)
        priority_combo.addItem("🔴 Высокий", 3)
        layout.addWidget(priority_label)
        layout.addWidget(priority_combo)
        
        # Чекбокс обязательности
        mandatory_check = QCheckBox("Обязательная задача")
        layout.addWidget(mandatory_check)
        
        # Кнопки
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        def save_task():
            title = title_edit.text().strip()
            if not title:
                QMessageBox.warning(self, 'Ошибка', 'Введите название задачи')
                return
            
            add_task(
                title=title,
                date=date.toString('yyyy-MM-dd'),
                description=desc_edit.toPlainText(),
                priority=priority_combo.currentData(),
                is_mandatory=mandatory_check.isChecked()
            )
            dialog.accept()
            self.load_week_tasks()
        
        save_btn.clicked.connect(save_task)
        cancel_btn.clicked.connect(dialog.reject)
        
        # Устанавливаем фокус на поле ввода
        title_edit.setFocus()
        
        dialog.exec()
    
    def set_date(self, date):
        """Установка даты начала недели"""
        self.current_date = date
        self.load_week_tasks()
    
    def prev_week(self):
        """Предыдущая неделя"""
        self.current_date = self.current_date.addDays(-7)
        self.load_week_tasks()
    
    def next_week(self):
        """Следующая неделя"""
        self.current_date = self.current_date.addDays(7)
        self.load_week_tasks()
    
    def close_dialog(self):
        """Закрытие диалога"""
        self.accept()