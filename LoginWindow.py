from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6 import QtGui
from ui.autorisation import Ui_MainWindow  # Импортируем ваш UI
from db import authenticate_user, get_users
from MainWindow import MainWindow  # Импортируем главное окно

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Настраиваем интерфейс
        self.setup_ui()
        
        # Подключаем сигналы
        self.connect_signals()
        
    def setup_ui(self):
        """Настройка интерфейса авторизации"""
        # Устанавливаем заголовок окна
        self.setWindowTitle("Семейный планировщик - Вход")
        
        # Настраиваем поле пароля
        self.ui.lineEdit_2.setEchoMode(QtGui.QLineEdit.EchoMode.Password)
        self.ui.lineEdit_2.setPlaceholderText("Введите пароль")
        
        # Настраиваем поле имени
        self.ui.lineEdit_3.setPlaceholderText("Введите имя пользователя")
        
        # Настраиваем кнопку показа пароля
        self.ui.pushButton.setText("👁")
        self.ui.pushButton.setToolTip("Показать/скрыть пароль")
        
        # Настраиваем кнопку входа
        self.ui.toolButton.setText("🚪 Войти")
        
        # Загружаем список пользователей в выпадающий список (если нужно)
        self.load_users()
        
        # Разрешаем Enter для входа
        self.ui.lineEdit_2.returnPressed.connect(self.login)
        self.ui.lineEdit_3.returnPressed.connect(self.login)
        
    def connect_signals(self):
        """Подключение сигналов"""
        self.ui.toolButton.clicked.connect(self.login)
        self.ui.pushButton.clicked.connect(self.toggle_password_visibility)
        
    def load_users(self):
        """Загрузка списка пользователей (опционально)"""
        try:
            users = get_users()
            # Если хотите сделать выпадающий список вместо поля ввода,
            # можно заменить lineEdit_3 на QComboBox
            print(f"Найдено пользователей: {len(users)}")
        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")
        
    def toggle_password_visibility(self):
        """Переключение видимости пароля"""
        if self.ui.lineEdit_2.echoMode() == QtGui.QLineEdit.EchoMode.Password:
            self.ui.lineEdit_2.setEchoMode(QtGui.QLineEdit.EchoMode.Normal)
            self.ui.pushButton.setText("🔒")
        else:
            self.ui.lineEdit_2.setEchoMode(QtGui.QLineEdit.EchoMode.Password)
            self.ui.pushButton.setText("👁")
            
    def login(self):
        """Обработка входа"""
        username = self.ui.lineEdit_3.text().strip()
        password = self.ui.lineEdit_2.text()
        
        # Проверяем введенные данные
        if not username:
            self.show_error("Введите имя пользователя")
            self.ui.lineEdit_3.setFocus()
            return
            
        if not password:
            self.show_error("Введите пароль")
            self.ui.lineEdit_2.setFocus()
            return
        
        # Показываем индикатор загрузки
        self.ui.toolButton.setText("⏳ Вход...")
        self.ui.toolButton.setEnabled(False)
        
        # Выполняем аутентификацию
        try:
            user_id = authenticate_user(username, password)
            
            if user_id:
                self.successful_login(user_id, username)
            else:
                self.failed_login()
                
        except Exception as e:
            self.show_error(f"Ошибка при входе: {str(e)}")
        finally:
            # Восстанавливаем кнопку
            self.ui.toolButton.setText("🚪 Войти")
            self.ui.toolButton.setEnabled(True)
    
    def successful_login(self, user_id, username):
        """Обработка успешного входа"""
        print(f"Успешный вход: {username} (ID: {user_id})")
        
        # Закрываем окно входа
        self.close()
        
        # Открываем главное окно
        self.main_window = MainWindow(user_id, username)
        self.main_window.show()
        
    def failed_login(self):
        """Обработка неудачного входа"""
        self.show_error("Неверное имя пользователя или пароль")
        
        # Очищаем поле пароля и устанавливаем фокус
        self.ui.lineEdit_2.clear()
        self.ui.lineEdit_2.setFocus()
        
    def show_error(self, message):
        """Показать сообщение об ошибке"""
        QMessageBox.warning(self, "Ошибка входа", message)
        
    def show_info(self, message):
        """Показать информационное сообщение"""
        QMessageBox.information(self, "Информация", message)