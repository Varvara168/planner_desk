from PyQt6.QtWidgets import (QDialog, QMessageBox, QInputDialog, QListWidgetItem, 
                             QAbstractItemView, QMenu, QInputDialog, QCheckBox, 
                             QHBoxLayout, QWidget, QPushButton, QVBoxLayout, QLabel,
                             QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6 import QtGui
from TaskEditorDialog import create_task_editor_dialog
from ui.taskdialog import Ui_Dialog
from db import (add_task, get_tasks_by_date, remove_task, toggle_task_status, 
                update_task, toggle_mandatory_status, get_categories, get_task_stats, get_task)

class TaskDialog(QDialog):
    def __init__(self, parent=None, user_id=1):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.user_id = user_id
        
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
        self.categories = get_categories(self.user_id)

        
    def set_date(self, date):
        """Установка даты и загрузка задач"""
        self.current_date = date
        self.setWindowTitle(f"Задачи на {date.toString('dd.MM.yyyy')}")
        self.load_tasks()
        
    def load_tasks(self):
        """Загрузка задач для текущей даты"""
        self.ui.listWidget.clear()
        tasks = get_tasks_by_date(self.current_date, self.user_id)
        
        print(f"📋 Всего задач: {len(tasks)}")
        
        for task in tasks:
            item = QListWidgetItem()
            
            # Получаем данные задачи
            status = "✅" if task['done'] else "❌"
            mandatory_indicator = "🔸 " if task['is_mandatory'] else ""
            priority_indicator = "⚡" * task.get('priority', 1)
            
            # Категория - будет справа
            category_name = task.get('category_name', '')
            if category_name:
                category_text = f" [{category_name}]"
            else:
                category_text = ""
            
            # Формируем текст задачи:
            # СЛЕВА: индикаторы + название | статус | СПРАВА: категория
            task_text = f"{mandatory_indicator}{priority_indicator} {task['title']} | {status}{category_text}"
            print(f"   📝 Задача: '{task_text}' (mandatory={task['is_mandatory']})")
            item.setText(task_text)
            item.setData(Qt.ItemDataRole.UserRole, task['id'])
            
            # 1. ПОДКРАШИВАЕМ ЦВЕТОМ КАТЕГОРИИ (весь текст)
            category_color = task.get('category_color')
            if category_color:
                try:
                    color = QtGui.QColor(category_color)
                    item.setForeground(color)
                    print(f"   🎨 Текст окрашен в цвет категории: {category_color}")
                except Exception as e:
                    print(f"   ❌ Ошибка цвета: {e}")
            
            # 2. ДОБАВЛЯЕМ ВСПЛЫВАЮЩУЮ ПОДСКАЗКУ С ОПИСАНИЕМ
            description = task.get('description', '')
            if description:
                # Создаем красивую всплывающую подсказку
                tooltip_text = f"📝 Описание:\n{description}"
                
                # Добавляем информацию о категории
                if category_name:
                    tooltip_text += f"\n\n🏷️ Категория: {category_name}"
                
                # Добавляем приоритет
                priority_text = {
                    1: "🟢 Низкий",
                    2: "🟡 Средний", 
                    3: "🔴 Высокий"
                }.get(task.get('priority', 1), "⚪ Не указан")
                
                tooltip_text += f"\n⚡ Приоритет: {priority_text}"
                
                # Добавляем дату создания
                if task.get('created_at'):
                    tooltip_text += f"\n📅 Создана: {task['created_at']}"
                
                item.setToolTip(tooltip_text)
            
            # 3. СТИЛЬ ДЛЯ ВЫПОЛНЕННЫХ ЗАДАЧ
            if task['done']:
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                # Для выполненных задач делаем более светлый цвет
                current_color = item.foreground().color()
                lighter_color = QtGui.QColor(
                    min(current_color.red() + 100, 255),
                    min(current_color.green() + 100, 255),
                    min(current_color.blue() + 100, 255)
                )
                item.setForeground(lighter_color)
            
            self.ui.listWidget.addItem(item)
        
        print("=" * 50)
    
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
        dialog = create_task_editor_dialog(
            parent=self,
            mode='add',
            date=self.current_date,
            user_id=self.user_id
        )
        
        if dialog.exec():
            self.load_tasks()

            
    def show_context_menu(self, position):
        """Показ контекстного меню для редактирования"""
        item = self.ui.listWidget.itemAt(position)
        if not item:
            return
            
        task_id = item.data(Qt.ItemDataRole.UserRole)
        task_info = get_task(task_id, self.user_id)

        
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
        """Редактирование задачи - используем ОБЩУЮ функцию как в неделях"""
        # Отладка: проверяем что приходит
        print(f"🔍 TaskDialog edit: ID={task_info.get('id')}, Category ID={task_info.get('category_id')}, Name={task_info.get('category_name')}")
        
        # Используем ТУ ЖЕ функцию что и в WeekDialog
        dialog = create_task_editor_dialog(
            parent=self,
            mode='edit',
            task_data=task_info,  # ← передаем ВСЕ данные задачи
            user_id=self.user_id
        )
        
        if dialog.exec():
            self.load_tasks()


    def change_priority(self, task_id, priority):
        """Изменение приоритета задачи"""
        if update_task(self.user_id, task_id, priority=priority):  # ← user_id ПЕРВЫЙ для update_task
            self.load_tasks()

    def update_enhanced_task(self, dialog, task_id, title, description, category_id, priority):
        """Обновление задачи с расширенными параметрами"""
        if not title.strip():
            QMessageBox.warning(self, 'Ошибка', 'Введите название задачи')
            return
        
        if update_task(
            user_id=self.user_id,  # ← user_id ПЕРВЫЙ
            task_id=task_id,      # ← task_id ВТОРОЙ
            title=title.strip(),
            description=description.strip(),
            category_id=category_id,
            priority=priority
        ):
            dialog.accept()
            self.load_tasks()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось обновить задачу')
    
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
            remove_task(self.user_id, task_id)
            self.load_tasks()
        
    def toggle_task_done(self, index):
        """Отметка задачи как выполненной/невыполненной"""
        item = self.ui.listWidget.item(index.row())
        task_id = item.data(Qt.ItemDataRole.UserRole)
        toggle_task_status(task_id, self.user_id)  # ← task_id ПЕРВЫЙ!
        self.load_tasks()

    def toggle_specific_task(self, item):
        """Изменение статуса задачи через контекстное меню"""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        toggle_task_status(task_id, self.user_id)  # ← task_id ПЕРВЫЙ!
        self.load_tasks()
    
    def toggle_mandatory_status(self, task_info, item):
        """Переключение статуса обязательности задачи"""
        print(f"🔄 Toggle mandatory для задачи {task_info['id']}")
        
        # Меняем в БД
        new_status = toggle_mandatory_status(task_info['id'], self.user_id)
        print(f"📊 toggle_mandatory_status вернул: {new_status} (type: {type(new_status)})")
        
        # ПРОВЕРЯЕМ НА None (ошибка), а не на False!
        if new_status is not None:  # Изменил с "is not False" на "is not None"
            updated_task_info = get_task(task_info['id'], self.user_id)
            
            if updated_task_info:
                status = "✅" if updated_task_info['done'] else "❌"
                mandatory_indicator = "🔸 " if updated_task_info['is_mandatory'] else ""
                priority_indicator = "⚡" * updated_task_info.get('priority', 1)
                
                category_name = updated_task_info.get('category_name', '')
                category_text = f" [{category_name}]" if category_name else ""
                
                task_text = f"{mandatory_indicator}{priority_indicator} {updated_task_info['title']} | {status}{category_text}"
                item.setText(task_text)
                
                print(f"✅ UI обновлен: {task_text}")
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось изменить статус задачи')
    def close_dialog(self):
        """Закрытие диалога"""
        self.close()
        
    def show(self):
        """Переопределяем show для обновления задач при каждом открытии"""
        self.load_tasks()
        super().show()