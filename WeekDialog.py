from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QWidget, QFrame, QPushButton, 
                             QMenu, QInputDialog, QMessageBox, QLineEdit, 
                             QCheckBox, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6 import QtGui
from ui.week_dialog import Ui_WeekDialog
from db import get_tasks_by_week, add_task, update_task, remove_task, toggle_task_status, toggle_mandatory_status
from TaskEditorDialog import create_task_editor_dialog


class WeekDialog(QDialog):
    def __init__(self, parent=None, user_id=1):
        super().__init__(parent)
        self.ui = Ui_WeekDialog()
        self.ui.setupUi(self)
        self.user_id = user_id
        
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
        
        self.tasks_by_day = get_tasks_by_week(self.current_date, self.user_id)
        
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

        task_frame.setFrameStyle(QFrame.Shape.NoFrame)
        
        is_mandatory = task.get('is_mandatory', False)
        is_done = task.get('done', False)
        priority = task.get('priority', 1)
        category_name = task.get('category_name', '')
        category_color = task.get('category_color', '')
        
        #  Определяем цвета по приоритету
        if priority == 3:  # Высокий
            bg_color = "#eb8686"  # Светло-красный
        elif priority == 2:  # Средний
            bg_color = "#f0d479"  # Светло-желтый
        else:  # Низкий
            bg_color = "#a7f3a7"  # Светло-зеленый
        
        # Если задача выполнена - серые цвета
        if is_done:
            bg_color = "#BEBEBE"  # Светло-серый
            text_color = "#525252"  # Темно-серый для текста
        else:
            text_color = "#000000"  # Черный текст
        
        # Если задача обязательная - добавляем акцент
        if is_mandatory and not is_done:
            bg_color = "#fdbb8f"  # Еще более красный

        # Устанавливаем стиль фрейма задачи
        task_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
            }}
        """)
        
        task_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        task_frame.customContextMenuRequested.connect(
            lambda pos, t=task, d=date: self.show_task_context_menu(pos, t, d)
        )
        
        task_layout = QHBoxLayout(task_frame)
        task_layout.setContentsMargins(5, 3, 5, 3)
        task_layout.setSpacing(8)
        
        # Статус задачи
        status = "✅" if is_done else "⏳"
        status_label = QLabel(status)
        if is_done:
            status_label.setStyleSheet("color: #666666;")
        
        # Иконка приоритета 
        priority_icon = QLabel()
        if priority == 3:
            priority_icon.setText("🔴")  # Красный кружок
        elif priority == 2:
            priority_icon.setText("🟡")  # Желтый кружок  
        else:
            priority_icon.setText("🟢")  # Зеленый кружок
        
        # Текст задачи
        task_text = QLabel(task.get('title', 'Без названия'))
        
        # Стиль для текста задачи
        text_style = f"color: {text_color};"
        if is_done:
            text_style += " text-decoration: line-through;"
        task_text.setStyleSheet(text_style)

        if task.get('category_id'):  
            print(f"   ✅ У задачи есть category_id: {task.get('category_id')}")
            
            category_name = task.get('category_name', '')
            
            # Создаем виджет для категории
            category_widget = QFrame()
            category_widget.setFrameStyle(QFrame.Shape.NoFrame)
            # Определяем цвет для плашки категории
            if is_done:
                # Для выполненных задач - серые цвета
                category_bg = "#cccccc"  # Темно-серый фон
                category_text_color = "#EEEEEE"  # Белый текст
            elif category_color:
                # Используем цвет категории
                category_bg = category_color
                category_text_color = "#EEEEEE"  # Белый текст
            else:
                # По умолчанию
                category_bg = "#e0e0e0"
                category_text_color = "#EEEEEE"
            
            # обрезаем название
            display_name = category_name
            if len(display_name) > 10:
                display_name = display_name[:8] + ".."
            
            category_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {category_bg};
                    border: none;
                    border-radius: 5px;
                    padding: 2px 6px;
                    min-width: 100px;
                    max-width: 200px;
                }}
            """)
            
            category_layout = QHBoxLayout(category_widget)
            category_layout.setContentsMargins(4, 2, 4, 2)
            
            # Текст категории
            category_label = QLabel(display_name)
            category_label.setStyleSheet(f"""
                QLabel {{
                    color: {category_text_color};
                    font-size: 13px;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Добавляем всплывающую подсказку с полным названием
            if len(category_name) > 10:
                category_widget.setToolTip(f"Категория: {category_name}")
            
            category_layout.addWidget(category_label)
            category_widget.setFixedHeight(40)
            category_widget.setMinimumWidth(140)
            category_widget.setMaximumWidth(200)
            
            print(f"   🎨 Создана плашка категории: '{display_name}' цвет: {category_bg}")
        else:
            category_widget = None
            print(f"   ❌ У задачи нет category_id")
        
        # 9. Добавляем элементы в layout
        task_layout.addWidget(status_label)
        task_layout.addWidget(priority_icon)
        task_layout.addWidget(task_text)
        task_layout.addStretch()  # Растягиваемое пространство
        
        if category_widget:
            task_layout.addWidget(category_widget)


        # 10. Добавляем всплывающую подсказку с описанием
        description = task.get('description', '')
        if description or category_name:
            tooltip_text = ""
            
            if description:
                tooltip_text += f"📝 Описание:\n{description}\n\n"
            
            if category_name:
                tooltip_text += f"🏷️ Категория: {category_name}\n"
            
            priority_text = {
                1: "🟢 Низкий",
                2: "🟡 Средний", 
                3: "🔴 Высокий"
            }.get(priority, "⚪ Не указан")
            
            tooltip_text += f"⚡ Приоритет: {priority_text}"
            
            if task.get('created_at'):
                tooltip_text += f"\n📅 Создана: {task['created_at']}"
            
            task_frame.setToolTip(tooltip_text)
        
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
            self.edit_task(task, date)
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
    
    def edit_task(self, task, date):
        """Редактирование задачи"""
        dialog = create_task_editor_dialog(
            parent=self,
            mode='edit',
            task_data=task,
            user_id=self.user_id
        )
        
        if dialog.exec():
            self.load_week_tasks()

    def delete_task(self, task):
        """Удаление задачи"""
        reply = QMessageBox.question(
            self, 
            'Подтверждение удаления',
            'Вы уверены, что хотите удалить эту задачу?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            remove_task(self.user_id, task['id'])
            self.load_week_tasks()
    
    def toggle_task(self, task):
        """Изменение статуса задачи"""
        toggle_task_status(task['id'], self.user_id)
        self.load_week_tasks()
    
    def toggle_mandatory_status(self, task):
        """Переключение статуса обязательности"""
        toggle_mandatory_status(task['id'], self.user_id)
        self.load_week_tasks()
    
    def set_task_priority(self, task, priority):
        """Установка приоритета задачи"""
        update_task(self.user_id, task['id'], priority=priority)
        self.load_week_tasks()
    
    def add_task_to_day(self, date):
        """Добавление задачи на день"""
        dialog = create_task_editor_dialog(
            parent=self,
            mode='add',
            date=date,
            user_id=self.user_id
        )
        
        if dialog.exec():
            self.load_week_tasks()
            
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
