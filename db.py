import sqlite3
import os
import json
from datetime import datetime, timedelta
import hashlib

def get_db_path():
    """Получение пути к базе данных"""
    return 'data/planner.db'

def init_db():
    """Инициализация базы данных с поддержкой пользователей"""
    db_path = get_db_path()
    
    # Создаем папку data если её нет
    os.makedirs('data', exist_ok=True)
    
    # Проверяем, существует ли база данных
    db_exists = os.path.exists(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица задач с привязкой к пользователю
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        task_date TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 1,
        is_mandatory BOOLEAN DEFAULT FALSE,
        done BOOLEAN DEFAULT FALSE,
        category_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
''')

    
    # Таблица категорий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            color TEXT DEFAULT '#007acc',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, name)
        )
    ''')
    
    # Таблица шаблонов задач
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, name),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
    
    # Таблица настроек пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            auto_backup BOOLEAN DEFAULT TRUE,
            notifications BOOLEAN DEFAULT TRUE,
            week_start TEXT DEFAULT 'monday',
            theme TEXT DEFAULT 'light',
            language TEXT DEFAULT 'ru',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Создаем индексы для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_date ON tasks(user_id, task_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_done ON tasks(user_id, done)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_priority ON tasks(user_id, priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id)')
    
    # Создаем администратора по умолчанию если база новая
    if not db_exists:
        admin_password_hash = hash_password("admin")
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            ('Admin', admin_password_hash)
        )
        admin_id = cursor.lastrowid
        
        # Создаем настройки для администратора
        cursor.execute(
            'INSERT INTO user_settings (user_id) VALUES (?)',
            (admin_id,)
        )
        
        # Создаем стандартные категории для администратора
        default_categories = [
            ('Работа', '#ff6b6b'),
            ('Личное', '#4ecdc4'),
            ('Здоровье', '#45b7d1'),
            ('Обучение', '#96ceb4'),
            ('Семья', '#feca57'),
            ('Другое', '#a29bfe')
        ]
        
        for name, color in default_categories:
            cursor.execute(
                'INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)',
                (admin_id, name, color)
            )
    
    conn.commit()
    conn.close()
    
    # Создаем папки для бэкапов и экспортов
    os.makedirs('data/backups', exist_ok=True)
    os.makedirs('data/exports', exist_ok=True)
    
    print(f"База данных {'создана' if not db_exists else 'подключена'}: {db_path}")

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========

def hash_password(password: str) -> str:
    salt = "planner_salt_v1"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def create_user(username, password):
    """Создание нового пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        user_id = cursor.lastrowid
        
        # Создаем настройки по умолчанию
        cursor.execute(
            'INSERT INTO user_settings (user_id) VALUES (?)',
            (user_id,)
        )
        
        # Создаем стандартные категории для нового пользователя
        default_categories = [
            ('Работа', '#ff6b6b'),
            ('Личное', '#4ecdc4'),
            ('Здоровье', '#45b7d1'),
            ('Обучение', '#96ceb4'),
            ('Семья', '#feca57'),
            ('Другое', '#a29bfe')
        ]
        
        for name, color in default_categories:
            cursor.execute(
                'INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)',
                (user_id, name, color)
            )
        
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None  # Пользователь уже существует
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return None
    finally:
        conn.close()

def authenticate_user(username, password):
    """Аутентификация пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Ошибка при аутентификации: {e}")
        return None
    finally:
        conn.close()

def get_users():
    """Получение списка пользователей"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, username FROM users ORDER BY username')
        users = cursor.fetchall()
        return [{'id': row[0], 'username': row[1]} for row in users]
    except Exception as e:
        print(f"Ошибка при получении пользователей: {e}")
        return []
    finally:
        conn.close()

def get_user_settings(user_id):
    """Получение настроек пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return {
                'user_id': result[0],
                'auto_backup': bool(result[1]),
                'notifications': bool(result[2]),
                'week_start': result[3],
                'theme': result[4],
                'language': result[5]
            }
        return None
    except Exception as e:
        print(f"Ошибка при получении настроек: {e}")
        return None
    finally:
        conn.close()

def update_user_settings(user_id, auto_backup=None, notifications=None, week_start=None, theme=None, language=None):
    """Обновление настроек пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if auto_backup is not None:
            updates.append("auto_backup = ?")
            params.append(auto_backup)
        if notifications is not None:
            updates.append("notifications = ?")
            params.append(notifications)
        if week_start is not None:
            updates.append("week_start = ?")
            params.append(week_start)
        if theme is not None:
            updates.append("theme = ?")
            params.append(theme)
        if language is not None:
            updates.append("language = ?")
            params.append(language)
            
        params.append(user_id)
        
        cursor.execute(f'''
            UPDATE user_settings 
            SET {', '.join(updates)}
            WHERE user_id = ?
        ''', params)
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении настроек: {e}")
        return False
    finally:
        conn.close()

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАДАЧАМИ ==========

def add_task(title, task_date, user_id, description="", category_id=None, priority=1, is_mandatory=False):
    """Добавление задачи"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO tasks (user_id, title, task_date, description, category_id, priority, is_mandatory)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, task_date, description, category_id, priority, is_mandatory))
        
        task_id = cursor.lastrowid
        conn.commit()
        print(f"Задача добавлена (ID: {task_id}) для пользователя {user_id}")
        return task_id
    except Exception as e:
        print(f"Ошибка при добавлении задачи: {e}")
        return None
    finally:
        conn.close()



def get_tasks_by_date(date_obj, user_id):
    """Получение задач по дате для конкретного пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        if hasattr(date_obj, 'toString'):
            date_str = date_obj.toString('yyyy-MM-dd')
        else:
            date_str = date_obj.strftime('%Y-%m-%d')
            
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE task_date = ? AND user_id = ?
            ORDER BY is_mandatory DESC, priority DESC, created_at
        ''', (date_str, user_id))
        
        tasks = cursor.fetchall()
        return [{
            'id': task[0], 'user_id': task[1], 'title': task[2],
            'task_date': task[3], 'description': task[4], 'priority': task[5],
            'is_mandatory': bool(task[6]), 'done': bool(task[7]),
            'created_at': task[8], 'updated_at': task[9]
        } for task in tasks]
    except Exception as e:
        print(f"Ошибка при получении задач: {e}")
        return []
    finally:
        conn.close()

def get_tasks_by_week(start_date, user_id):
    """Получение задач на неделю для конкретного пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Вычисляем дату окончания недели (start_date + 6 дней)
        if hasattr(start_date, 'addDays'):
            end_date = start_date.addDays(6)
            start_date_str = start_date.toString('yyyy-MM-dd')
            end_date_str = end_date.toString('yyyy-MM-dd')
        else:
            end_date = start_date + timedelta(days=6)
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE task_date BETWEEN ? AND ? AND user_id = ?
            ORDER BY task_date, is_mandatory DESC, priority DESC
        ''', (start_date_str, end_date_str, user_id))
        
        tasks = cursor.fetchall()
        
        # Группируем задачи по дням
        tasks_by_day = {}
        for task in tasks:
            day = task[3]  # task_date
            if day not in tasks_by_day:
                tasks_by_day[day] = []
            tasks_by_day[day].append({
                'id': task[0], 'user_id': task[1], 'title': task[2],
                'task_date': task[3], 'description': task[4], 'priority': task[5],
                'is_mandatory': bool(task[6]), 'done': bool(task[7]),
                'created_at': task[8], 'updated_at': task[9]
            })
        
        return tasks_by_day
    except Exception as e:
        print(f"Ошибка при получении задач на неделю: {e}")
        return {}
    finally:
        conn.close()

def update_task(task_id, user_id, title=None, description=None, task_date=None, priority=None, is_mandatory=None):
    """Обновление задачи"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if task_date is not None:
            updates.append("task_date = ?")
            params.append(task_date)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if is_mandatory is not None:
            updates.append("is_mandatory = ?")
            params.append(is_mandatory)
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)
        params.append(user_id)  # Добавляем проверку пользователя
        
        cursor.execute(f'''
            UPDATE tasks 
            SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
        ''', params)
        
        conn.commit()
        print(f"Задача {task_id} обновлена")
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка при обновлении задачи: {e}")
        return False
    finally:
        conn.close()

def remove_task(task_id, user_id):
    """Удаление задачи по ID с проверкой пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            print(f"Задача {task_id} удалена пользователем {user_id}")
        return deleted
    except Exception as e:
        print(f"Ошибка при удалении задачи: {e}")
        return False
    finally:
        conn.close()

def toggle_task_status(task_id, user_id):
    """Переключение статуса выполнения задачи"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Получаем текущий статус
        cursor.execute('SELECT done FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        result = cursor.fetchone()
        
        if result is None:
            print(f"Задача {task_id} не найдена для пользователя {user_id}")
            return False
            
        current_status = result[0]
        
        # Инвертируем статус
        cursor.execute('UPDATE tasks SET done = ? WHERE id = ? AND user_id = ?', 
                      (not current_status, task_id, user_id))
        conn.commit()
        
        print(f"Статус задачи {task_id} изменен на {not current_status}")
        return not current_status
    except Exception as e:
        print(f"Ошибка при изменении статуса задачи: {e}")
        return False
    finally:
        conn.close()

def save_template(user_id, name, template_data):
    """Сохранение шаблона задач"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''
            INSERT OR REPLACE INTO templates (user_id, name, data)
            VALUES (?, ?, ?)
            ''',
            (user_id, name, json.dumps(template_data, ensure_ascii=False))
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка сохранения шаблона: {e}")
        return False
    finally:
        conn.close()

def get_available_templates(user_id):
    """Получение списка шаблонов пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT name FROM templates WHERE user_id = ? ORDER BY name',
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Ошибка получения шаблонов: {e}")
        return []
    finally:
        conn.close()


def get_task(task_id, user_id):
    """Получение одной задачи по ID с проверкой пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''
            SELECT * FROM tasks
            WHERE id = ? AND user_id = ?
            ''',
            (task_id, user_id)
        )

        task = cursor.fetchone()
        if not task:
            return None

        return {
            'id': task[0],
            'user_id': task[1],
            'title': task[2],
            'task_date': task[3],
            'description': task[4],
            'priority': task[5],
            'is_mandatory': bool(task[6]),
            'done': bool(task[7]),
            'created_at': task[8],
            'updated_at': task[9]
        }
    except Exception as e:
        print(f"Ошибка при получении задачи: {e}")
        return None
    finally:
        conn.close()


def toggle_mandatory_status(task_id, user_id):
    """Переключение статуса обязательности задачи"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Получаем текущий статус
        cursor.execute('SELECT is_mandatory FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        result = cursor.fetchone()
        
        if result is None:
            print(f"Задача {task_id} не найдена для пользователя {user_id}")
            return False
            
        current_status = result[0]
        
        # Инвертируем статус
        cursor.execute('UPDATE tasks SET is_mandatory = ? WHERE id = ? AND user_id = ?', 
                      (not current_status, task_id, user_id))
        conn.commit()
        
        print(f"Статус обязательности задачи {task_id} изменен на {not current_status}")
        return not current_status
    except Exception as e:
        print(f"Ошибка при изменении статуса обязательности: {e}")
        return False
    finally:
        conn.close()

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С КАТЕГОРИЯМИ ==========

def get_categories(user_id):
    """Получение всех категорий пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ? ORDER BY name', (user_id,))
        categories = cursor.fetchall()
        return [{'id': cat[0], 'name': cat[1], 'color': cat[2]} for cat in categories]
    except Exception as e:
        print(f"Ошибка при получении категорий: {e}")
        return []
    finally:
        conn.close()

def add_category(name, user_id, color='#007acc'):
    """Добавление категории"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)', 
                      (user_id, name, color))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # Категория с таким именем уже существует
    except Exception as e:
        print(f"Ошибка при добавлении категории: {e}")
        return None
    finally:
        conn.close()

def update_category(category_id, user_id, name, color):
    """Обновление категории"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE categories 
            SET name = ?, color = ? 
            WHERE id = ? AND user_id = ?
        ''', (name, color, category_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка при обновлении категории: {e}")
        return False
    finally:
        conn.close()

def delete_category(category_id, user_id):
    """Удаление категории"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Сначала обнуляем category_id у задач пользователя
        cursor.execute('UPDATE tasks SET category_id = NULL WHERE category_id = ? AND user_id = ?', 
                      (category_id, user_id))
        # Удаляем категорию
        cursor.execute('DELETE FROM categories WHERE id = ? AND user_id = ?', (category_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка при удалении категории: {e}")
        return False
    finally:
        conn.close()

# ========== СТАТИСТИКА И ОТЧЕТЫ ==========

def get_task_stats(user_id):
    """Получение статистики по задачам пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Общее количество задач
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ?', (user_id,))
        total_tasks = cursor.fetchone()[0]
        
        # Выполненные задачи
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND done = 1', (user_id,))
        completed_tasks = cursor.fetchone()[0]
        
        # Задачи на сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND task_date = ?', (user_id, today))
        today_tasks = cursor.fetchone()[0]
        
        # Просроченные задачи
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND task_date < ? AND done = 0', 
                      (user_id, today))
        overdue_tasks = cursor.fetchone()[0]
        
        # Задачи по приоритетам
        cursor.execute('SELECT priority, COUNT(*) FROM tasks WHERE user_id = ? GROUP BY priority', (user_id,))
        priority_stats = cursor.fetchall()
        
        return {
            'total': total_tasks,
            'completed': completed_tasks,
            'today': today_tasks,
            'overdue': overdue_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'priority_stats': {priority: count for priority, count in priority_stats}
        }
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return {'total': 0, 'completed': 0, 'today': 0, 'overdue': 0, 'completion_rate': 0, 'priority_stats': {}}
    finally:
        conn.close()

# ========== ЭКСПОРТ И ИМПОРТ ==========

def export_tasks_to_json(user_id, filename=None):
    """Экспорт задач пользователя в JSON файл"""
    export_dir = "data/exports"
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if not filename:
        # Если имени файла нет, генерируем безопасное
        filename = f"backup_{user_id}_{timestamp}.json"
    else:
        # Если передано имя/путь, берем только имя файла
        filename = os.path.basename(filename)

    file_path = os.path.join(export_dir, filename)

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY task_date', (user_id,))
        tasks = cursor.fetchall()

        categories = get_categories(user_id)

        export_data = {
            'export_date': datetime.now().isoformat(),
            'user_id': user_id,
            'version': '2.0',
            'tasks_count': len(tasks),
            'categories': categories,
            'tasks': [{
                'id': task[0], 'user_id': task[1], 'title': task[2],
                'task_date': task[3], 'description': task[4], 'priority': task[5],
                'is_mandatory': bool(task[6]), 'done': bool(task[7]),
                'created_at': task[8], 'updated_at': task[9]
            } for task in tasks]
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"Задачи пользователя {user_id} экспортированы в {file_path}")
        return True
    except Exception as e:
        print(f"Ошибка при экспорте задач: {e}")
        return False
    finally:
        conn.close()

def import_tasks_from_json(user_id, filename):
    """Импорт задач из JSON файла для пользователя"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        for task_data in data.get('tasks', []):
            # Пропускаем ID при импорте, используем текущего пользователя
            add_task(
                title=task_data['title'],
                task_date=task_data['task_date'],
                user_id=user_id,
                description=task_data.get('description', ''),
                priority=task_data.get('priority', 1),
                is_mandatory=task_data.get('is_mandatory', False)
            )
            imported_count += 1
        
        print(f"Импортировано {imported_count} задач для пользователя {user_id}")
        return True
    except Exception as e:
        print(f"Ошибка при импорте задач: {e}")
        return False

def clear_all_tasks(user_id):
    """Очистка всех задач пользователя"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM tasks WHERE user_id = ?', (user_id,))
        conn.commit()
        deleted_count = cursor.rowcount
        print(f"Удалено {deleted_count} задач пользователя {user_id}")
        return True
    except Exception as e:
        print(f"Ошибка при очистке задач: {e}")
        return False
    finally:
        conn.close()

# ========== АВТО-БЭКАП ==========

def auto_backup(user_id):
    """Автоматическое создание бэкапа для пользователя"""
    try:
        settings = get_user_settings(user_id)
        if settings and settings.get('auto_backup', True):
            backup_file = f"data/backups/auto_backup_{user_id}_{datetime.now().strftime('%Y%m%d')}.json"
            return export_tasks_to_json(user_id, backup_file)
        return True
    except Exception as e:
        print(f"Ошибка при автоматическом бэкапе: {e}")
        return False