import sqlite3
import threading
from typing import List, Dict, Any, Optional


class Database:
    _instance = None
    _lock = threading.Lock()
    _connection = None

    def __new__(cls, db_path: str):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance._connection = None
            return cls._instance

    def connect(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row

    def execute(self, sql: str, parameters: tuple = (), fetchone=False, fetchall=False, commit=False):
        if self._connection is None:
            self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute(sql, parameters)
        
        data = None
        if fetchone:
            data = cursor.fetchone()
        elif fetchall:
            data = cursor.fetchall()
        
        if commit:
            self._connection.commit()
            
        cursor.close()
        return data

    def create_tables(self):
        """Створення всіх необхідних таблиць."""
        self.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """, commit=True)

        self.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """, commit=True)

        self.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            event_date TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """, commit=True)

    # ---- Функції для користувачів ----
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str) -> None:
        sql = """
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name
        """
        self.execute(sql, (user_id, username, first_name, last_name), commit=True)

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM users WHERE user_id = ?"
        result = self.execute(sql, (user_id,), fetchone=True)
        if result:
            return dict(result)
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM users"
        result = self.execute(sql, fetchall=True)
        return [dict(row) for row in result]

    # ---- Функції для нагадувань ----
    def add_reminder(self, user_id: int, text: str, remind_at: str) -> None:
        sql = """
        INSERT INTO reminders (user_id, text, remind_at)
        VALUES (?, ?, ?)
        """
        self.execute(sql, (user_id, text, remind_at), commit=True)

    def get_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM reminders WHERE user_id = ? ORDER BY remind_at ASC"
        result = self.execute(sql, (user_id,), fetchall=True)
        return [dict(row) for row in result]

    def delete_reminder(self, reminder_id: int) -> None:
        sql = "DELETE FROM reminders WHERE id = ?"
        self.execute(sql, (reminder_id,), commit=True)

    # ---- Функції для подій ----
    def add_event(self, user_id: int, title: str, description: str, event_date: str) -> None:
        sql = """
        INSERT INTO events (user_id, title, description, event_date)
        VALUES (?, ?, ?, ?)
        """
        self.execute(sql, (user_id, title, description, event_date), commit=True)

    def get_events(self, user_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM events WHERE user_id = ? ORDER BY event_date ASC"
        result = self.execute(sql, (user_id,), fetchall=True)
        return [dict(row) for row in result]

    def delete_event(self, event_id: int) -> None:
        sql = "DELETE FROM events WHERE id = ?"
        self.execute(sql, (event_id,), commit=True)
