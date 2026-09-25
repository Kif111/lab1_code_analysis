# student_portal_secure.py
import os
import sqlite3
import hashlib
import logging
from pathlib import Path

UPLOAD_DIR = Path("uploads").resolve()
API_KEY = os.getenv("AI_API_KEY")  # секрет — из переменных окружения

logging.basicConfig(filename="portal.log", level=logging.INFO)


def authenticate(username: str, password: str):
    """Проверяет пользователя по параметризованному запросу."""
    with sqlite3.connect("university.db") as db:
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, role, password_hash FROM users WHERE username = ?",
            (username,),
        )
        user = cursor.fetchone()
        # В продакшене: Argon2 / bcrypt / PBKDF2 с уникальной солью
        return user if user and verify_password(password, user[2]) else None


def verify_password(password: str, stored_hash: str) -> bool:
    """Проверка пароля (заглушка — в реальности PBKDF2/bcrypt)."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), b"salt", 100_000).hex() == stored_hash


def require_role(user, expected_role: str) -> bool:
    return user is not None and user[1] == expected_role


def safe_read_uploaded_file(filename: str) -> str:
    """Защита от path traversal через normalize + проверку префикса."""
    requested_path = (UPLOAD_DIR / filename).resolve()
    if not str(requested_path).startswith(str(UPLOAD_DIR)):
        raise ValueError("Invalid file path")
    with open(requested_path, "r", encoding="utf-8") as f:
        return f.read()


def view_grade(student_id: int):
    with sqlite3.connect("university.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT grade FROM grades WHERE student_id = ?", (student_id,))
        return cursor.fetchone()


def delete_student(student_id: int, user):
    if not require_role(user, "admin"):
        return "denied"
    with sqlite3.connect("university.db") as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        db.commit()
    return "deleted"


def save_comment(username: str, comment: str):
    if not comment:
        return "empty"
    with sqlite3.connect("university.db") as db:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO comments (username, comment) VALUES (?, ?)",
            (username, comment),
        )
        db.commit()
    return "saved"


def hash_password(password: str) -> str:
    """Безопасное хеширование с солью."""
    import secrets
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + digest.hex()


def log_login_attempt(username: str, success: bool) -> None:
    """Логируем только факт, без пароля."""
    logging.info("Login attempt: user=%s, success=%s", username, success)


def process_student_request(action, username, password, student_id, role, comment, filename):
    """Диспетчер: делегирует в мелкие функции, не содержит бизнес-логики."""
    user = authenticate(username, password)
    log_login_attempt(username, user is not None)
    if not user:
        return "login failed"

    handlers = {
        "view_grade": lambda: view_grade(student_id),
        "delete_student": lambda: delete_student(student_id, user),
        "save_comment": lambda: save_comment(username, comment),
        "open_file": lambda: safe_read_uploaded_file(filename),
        "hash_password": lambda: hash_password(password),
    }
    return handlers.get(action, lambda: "unknown action")()
