from PyQt6.QtWidgets import QApplication, QMainWindow, QCalendarWidget, QMessageBox
from PyQt6.QtCore import QDate, QTimer, QEvent
from PyQt6 import QtCore, QtGui, QtWidgets
from ui.main_window import Ui_MainWindow
from TaskDialog import TaskDialog
from WeekDialog import WeekDialog
from CategoryDialog import CategoryDialog
from ExportDialog import ExportDialog
from db import init_db, clear_all_tasks, get_task_stats, get_user_settings, update_user_settings
import os

class MainWindow(QMainWindow):
    def __init__(self, parent=None, user_id=1):
        super().__init__()
        
        # Создаем папки для данных
        self.create_data_folders()
        self.user_id = user_id
        
        # Инициализация базы данных ПЕРВЫМ делом
        try:
            init_db()
            print("База данных успешно инициализирована")
        except Exception as e:
            QMessageBox.critical(
                None, 
                'Ошибка базы данных', 
                f'Не удалось инициализировать базу данных: {e}'
            )
            return
        
        # Инициализация интерфейса
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Создание календаря
        self.calendar = QCalendarWidget(self.ui.widget)
        self.calendar.setGeometry(0, 0, self.ui.widget.width(), self.ui.widget.height())
        self.calendar.setGridVisible(True)
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        # Настройка стилей для календаря
        self.setup_calendar_styles()
        
        # Текущая дата
        self.calendar.setSelectedDate(QDate.currentDate())
        
        # Переменные для отслеживания состояния
        self.current_selected_date = QDate.currentDate()
        self.dialog_opened_date = None
        self.is_dialog_open = False
        self.focus_protection_enabled = True

        # Центрируем заголовок месяца
        self.ui.label_date.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.update_month_label()

        # Переименовываем кнопки для ясности
        self.ui.pushButton_3.setText("Очистить всё")
        self.ui.pushButton_4.setText("Неделя")
        self.ui.pushButton_5.setText("Сегодня")
        self.ui.pushButton_6.setText("📤")  # Переименовываем pushButton_6

        # Добавляем новые кнопки
        self.setup_enhanced_ui()

        # Создаём диалоговые окна
        self.task_dialog = TaskDialog(user_id=self.user_id)
        self.week_dialog = WeekDialog(self)
        self.category_dialog = CategoryDialog(self)
        self.export_dialog = ExportDialog(self)
        
        # Настраиваем диалоги как немодальные и без захвата фокуса
        self.setup_dialogs()

        # Устанавливаем фильтр событий для диалогов
        self.task_dialog.installEventFilter(self)
        self.week_dialog.installEventFilter(self)
        self.category_dialog.installEventFilter(self)
        self.export_dialog.installEventFilter(self)

        # Подключаем кнопки к методам
        self.ui.btn_prev.clicked.connect(self.prev_month)
        self.ui.btn_next.clicked.connect(self.next_month)
        self.ui.pushButton_5.clicked.connect(self.go_to_today)
        self.ui.pushButton_3.clicked.connect(self.clear_all_tasks)
        self.ui.pushButton_4.clicked.connect(self.show_week_view)
        self.ui.pushButton_6.clicked.connect(self.show_export)  # Подключаем pushButton_6 к экспорту

        # Подключаем новые кнопки
        self.categories_btn.clicked.connect(self.show_categories)
        self.settings_btn.clicked.connect(self.show_settings)
        self.stats_btn.clicked.connect(self.show_statistics)

        # События календаря
        self.calendar.selectionChanged.connect(self.day_selection_changed)
        self.calendar.clicked.connect(self.date_clicked)
        self.calendar.activated.connect(self.date_activated)
        
        # События диалога задач
        self.task_dialog.finished.connect(self.on_task_dialog_closed)
        
        # Авто-бэкап при запуске
        self.auto_backup()
        
        # Показываем статистику при запуске
        self.show_startup_stats()
        
        # Обновляем стили для начального состояния
        self.update_calendar_styles()

    def create_data_folders(self):
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
        print("Папки для данных созданы")

    def setup_enhanced_ui(self):
        """Настройка улучшенного интерфейса с дополнительными кнопками"""
        # Создаем layout для дополнительных кнопок
        additional_buttons_layout = QtWidgets.QHBoxLayout()
        
        # Кнопка категорий
        self.categories_btn = QtWidgets.QPushButton("📂 Категории")
        self.categories_btn.setToolTip("Управление категориями задач")
        
        # Кнопка настроек
        self.settings_btn = QtWidgets.QPushButton("⚙️ Настройки")
        self.settings_btn.setToolTip("Настройки приложения")
        
        # Кнопка статистики
        self.stats_btn = QtWidgets.QPushButton("📊 Статистика")
        self.stats_btn.setToolTip("Просмотр статистики")
        
        additional_buttons_layout.addWidget(self.categories_btn)
        additional_buttons_layout.addWidget(self.settings_btn)
        additional_buttons_layout.addWidget(self.stats_btn)
        additional_buttons_layout.addStretch()
        
        # Добавляем layout в основной интерфейс
        main_layout = self.ui.centralwidget.layout()
        if main_layout:
            # Вставляем после существующих кнопок
            main_layout.insertLayout(2, additional_buttons_layout)

    def auto_backup(self):
        """Автоматическое создание бэкапа"""
        settings = get_user_settings(self.user_id)
        if settings and settings.get('auto_backup', True):
            from db import export_tasks_to_json
            backup_file = f"data/backups/auto_backup_{self.user_id}_{QDate.currentDate().toString('yyyyMMdd')}.json"
            if export_tasks_to_json(self.user_id, backup_file):
                print("Автоматический бэкап создан")
            else:
                print("Не удалось создать автоматический бэкап")

    def show_categories(self):
        """Показать диалог категорий"""
        self.category_dialog.show()
        self.category_dialog.raise_()
        QTimer.singleShot(0, self.return_focus_to_calendar)

    def show_export(self):
        """Показать диалог экспорта"""
        self.export_dialog.show()
        self.export_dialog.raise_()
        QTimer.singleShot(0, self.return_focus_to_calendar)

    def show_settings(self):
        """Показать настройки"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QMessageBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        dialog.setModal(True)
        dialog.resize(300, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Получаем настройки текущего пользователя
        user_id = 1  # TODO: замените на текущего пользователя
        settings = get_user_settings(user_id) or {}
        
        # Настройки
        auto_backup_cb = QCheckBox("Автоматический бэкап при запуске")
        auto_backup_cb.setChecked(settings.get('auto_backup', True))
        
        notifications_cb = QCheckBox("Уведомления о задачах")
        notifications_cb.setChecked(settings.get('notifications', True))
        
        week_start_monday = QCheckBox("Неделя начинается с понедельника")
        week_start_monday.setChecked(settings.get('week_start', 'monday') == 'monday')
        
        layout.addWidget(auto_backup_cb)
        layout.addWidget(notifications_cb)
        layout.addWidget(week_start_monday)
        layout.addStretch()
        
        # Кнопки
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        
        def save_settings():
            update_user_settings(
                user_id,
                auto_backup=auto_backup_cb.isChecked(),
                notifications=notifications_cb.isChecked(),
                week_start='monday' if week_start_monday.isChecked() else 'sunday'
            )
            dialog.accept()
            QMessageBox.information(self, 'Успех', 'Настройки сохранены')
        
        save_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()


    def show_statistics(self):
        """Показать расширенную статистику"""
        stats = get_task_stats(self.user_id)
        
        stats_text = f"""
📊 Детальная статистика:

📈 Общие показатели:
• Всего задач: {stats['total']}
• Выполнено: {stats['completed']} ({stats['completion_rate']:.1f}%)
• На сегодня: {stats['today']}
• Просрочено: {stats['overdue']}

⚡ Распределение по приоритетам:
• 🔴 Высокий: {stats['priority_stats'].get(3, 0)}
• 🟡 Средний: {stats['priority_stats'].get(2, 0)}
• 🟢 Низкий: {stats['priority_stats'].get(1, 0)}

📅 Продуктивность:
• Выполняемость: {stats['completion_rate']:.1f}%
• Активных задач: {stats['total'] - stats['completed']}
        """
        
        QMessageBox.information(self, 'Детальная статистика', stats_text.strip())

    # Остальные методы остаются без изменений
    def eventFilter(self, obj, event):
        """Фильтр событий для предотвращения автоматического захвата фокуса"""
        if (obj in [self.task_dialog, self.week_dialog, self.category_dialog, self.export_dialog] 
            and self.focus_protection_enabled):
            if event.type() == QEvent.Type.WindowActivate or event.type() == QEvent.Type.FocusIn:
                QTimer.singleShot(0, self.return_focus_to_calendar)
                return True
        return super().eventFilter(obj, event)

    def setup_dialogs(self):
        """Настройка диалогов для работы без захвата фокуса"""
        for dialog in [self.task_dialog, self.week_dialog, self.category_dialog, self.export_dialog]:
            dialog.setModal(False)
            dialog.setWindowFlags(
                QtCore.Qt.WindowType.Dialog | 
                QtCore.Qt.WindowType.CustomizeWindowHint |
                QtCore.Qt.WindowType.WindowTitleHint |
                QtCore.Qt.WindowType.WindowCloseButtonHint |
                QtCore.Qt.WindowType.WindowDoesNotAcceptFocus
            )

    def setup_calendar_styles(self):
        """Настройка стилей календаря"""
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: 1px solid #ccc;
            }
            QCalendarWidget QToolButton {
                color: #2c3e50;
                font-weight: bold;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #ccc;
            }
        """)
        
        today_format = QtGui.QTextCharFormat()
        today_format.setBackground(QtGui.QColor(255, 228, 225))
        today_format.setForeground(QtGui.QColor(199, 21, 133))
        self.calendar.setDateTextFormat(QDate.currentDate(), today_format)

    def update_calendar_styles(self):
        """Обновление стилей дат в календаре"""
        self.calendar.setDateTextFormat(QDate(), QtGui.QTextCharFormat())
        
        today_format = QtGui.QTextCharFormat()
        today_format.setBackground(QtGui.QColor(255, 228, 225))
        today_format.setForeground(QtGui.QColor(199, 21, 133))
        self.calendar.setDateTextFormat(QDate.currentDate(), today_format)
        
        if self.dialog_opened_date and self.dialog_opened_date.isValid():
            selected_format = QtGui.QTextCharFormat()
            if self.dialog_opened_date == QDate.currentDate():
                selected_format.setBackground(QtGui.QColor(219, 112, 147))
                selected_format.setForeground(QtGui.QColor(255, 255, 255))
            else:
                selected_format.setBackground(QtGui.QColor(220, 220, 220))
                selected_format.setForeground(QtGui.QColor(0, 0, 0))
            self.calendar.setDateTextFormat(self.dialog_opened_date, selected_format)

    def show_startup_stats(self):
        """Показать статистику при запуске"""
        stats = get_task_stats(self.user_id)
        self.ui.statusbar.showMessage(
            f"Задачи: всего {stats['total']} | выполнено {stats['completed']} | сегодня {stats['today']}"
        )

    def prev_month(self):
        """Переход на предыдущий месяц"""
        self.calendar.showPreviousMonth()
        self.update_month_label()
        self.update_calendar_styles()
        self.update_task_dialog_if_open()
        self.return_focus_to_calendar()

    def next_month(self):
        """Переход на следующий месяц"""
        self.calendar.showNextMonth()
        self.update_month_label()
        self.update_calendar_styles()
        self.update_task_dialog_if_open()
        self.return_focus_to_calendar()

    def update_month_label(self):
        """Обновление надписи месяца и года"""
        month = self.calendar.monthShown()
        year = self.calendar.yearShown()
        date = QDate(year, month, 1)
        self.ui.label_date.setText(date.toString("MMMM yyyy").capitalize())

    def day_selection_changed(self):
        """При изменении выбора даты"""
        date = self.calendar.selectedDate()
        self.current_selected_date = date
        self.update_month_label()
        self.update_task_dialog_if_open()
        self.return_focus_to_calendar()

    def date_clicked(self, date):
        """При клике на дату в календаре"""
        self.current_selected_date = date
        self.open_or_update_task_dialog(date)
        self.return_focus_to_calendar()

    def date_activated(self, date):
        """При активации даты"""
        self.current_selected_date = date
        self.open_or_update_task_dialog(date)
        self.return_focus_to_calendar()

    def open_or_update_task_dialog(self, date):
        """Открытие или обновление диалога задач"""
        if self.is_dialog_open:
            self.update_task_dialog(date)
        else:
            self.open_task_dialog(date)

    def open_task_dialog(self, date):
        """Открытие диалога задач"""
        self.focus_protection_enabled = False
        self.dialog_opened_date = date
        self.is_dialog_open = True
        self.update_calendar_styles()
        
        self.task_dialog.set_date(date)
        self.task_dialog.show()
        self.task_dialog.raise_()
        
        QTimer.singleShot(100, self.enable_focus_protection)
        QTimer.singleShot(0, self.return_focus_to_calendar)

    def update_task_dialog(self, date):
        """Обновление диалога задач"""
        self.dialog_opened_date = date
        self.update_calendar_styles()
        self.task_dialog.set_date(date)
        self.return_focus_to_calendar()

    def update_task_dialog_if_open(self):
        """Обновление диалога если он открыт"""
        if self.is_dialog_open:
            date = self.calendar.selectedDate()
            self.update_task_dialog(date)

    def return_focus_to_calendar(self):
        """Возвращает фокус на календарь"""
        if not self.calendar.hasFocus():
            self.calendar.setFocus()

    def enable_focus_protection(self):
        """Включает защиту фокуса"""
        self.focus_protection_enabled = True

    def on_task_dialog_closed(self, result):
        """Обработчик закрытия диалога задач"""
        self.dialog_opened_date = None
        self.is_dialog_open = False
        self.update_calendar_styles()
        self.return_focus_to_calendar()

    def go_to_today(self):
        """Переход к сегодняшней дате"""
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.current_selected_date = today
        self.update_month_label()
        
        if self.is_dialog_open:
            self.update_task_dialog(today)
        
        stats = get_task_stats(self.user_id)
        self.ui.statusbar.showMessage(f"Задач на сегодня: {stats['today']}")
        
        self.update_calendar_styles()
        self.return_focus_to_calendar()

    def clear_all_tasks(self):
        """Очистка всех задач с подтверждением"""
        reply = QMessageBox.question(
            self,
            'Очистка всех задач',
            'Вы уверены, что хотите удалить ВСЕ задачи? Это действие нельзя отменить.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if clear_all_tasks(self.user_id):
                QMessageBox.information(self, 'Успех', 'Все задачи удалены')
                self.show_startup_stats()
                if self.is_dialog_open:
                    self.task_dialog.load_tasks()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось очистить задачи')
        
        self.return_focus_to_calendar()

    def show_week_view(self):
        """Показать задачи на неделю"""
        try:
            print("Открытие недельного просмотра...")
            
            today = QDate.currentDate()
            days_to_monday = today.dayOfWeek() - 1
            week_start = today.addDays(-days_to_monday)
            
            # Создаем новый диалог каждый раз
            self.week_dialog = WeekDialog(self)
            self.week_dialog.set_date(week_start)
            
            # Просто показываем диалог
            self.week_dialog.exec()
            
            # Возвращаем фокус
            self.calendar.setFocus()
            
        except Exception as e:
            print(f"Ошибка при открытии недельного просмотра: {e}")
            QMessageBox.warning(self, 'Ошибка', f'Не удалось открыть недельный просмотр: {e}')

if __name__ == "__main__":
    app = QApplication([])
    
    try:
        window = MainWindow()
        window.show()
        app.exec()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        QMessageBox.critical(
            None, 
            'Ошибка приложения', 
            f'Не удалось запустить приложение: {e}'
        )