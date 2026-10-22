"""feedback_app_fixed.py - secure version of the feedback service."""
import html
import logging
import re
import sqlite3
from flask import Flask, abort, request

app = Flask(__name__)

# --- Настройки логирования (как в оригинале) ---
log = logging.getLogger("feedback")
log.setLevel(logging.INFO)
_handler = logging.FileHandler("feedback.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
log.addHandler(_handler)

DB = "feedback.db"

# --- Белые списки и лимиты ---
ALLOWED_SORT = {"rating", "name"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NAME_MAX = 100
COMMENT_MAX = 1000

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS feedback (name TEXT, email TEXT, rating INTEGER, comment TEXT)")

def safe_log_value(value):
    """Fix 5: убираем переводы строк, чтобы подделать лог было нельзя."""
    return str(value).replace("\n", " ").replace("\r", " ")

@app.route("/feedback", methods=['POST'])
def add_feedback():
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    rating_raw = request.form.get("rating", "")
    comment = request.form.get("comment", "")

    # Fix 2: Обрабатываем нечисловую оценку
    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        abort(400)

    # Fix 1: Проверка диапазона оценки
    if not 1 <= rating <= 5:
        abort(400)

    # Fix 6: Ограничение длины
    if len(comment) > COMMENT_MAX:
        abort(400)
    if not name or not name.strip() or len(name) > NAME_MAX:
        abort(400)

    # Fix 7: Валидация email
    if not EMAIL_RE.match(email):
        abort(400)

    # Запись в БД (параметризованный запрос)
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO feedback VALUES (?, ?, ?, ?)", (name, email, rating, comment))

    # Fix 5: Безопасное логирование
    log.info("feedback from %s: %s", safe_log_value(name), safe_log_value(comment))

    # Fix 3: Экранирование HTML при выводе
    return f'<p>Thank you, {html.escape(name)}! Your rating: {rating}</p>'

@app.route("/feedback")
def list_feedback():
    sort = request.args.get("sort", "rating")
    # Fix 4: Белый список для сортировки
    if sort not in ALLOWED_SORT:
        abort(400)
        
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(f"SELECT name, rating FROM feedback ORDER BY {sort}").fetchall()
    return {"feedback": [{"name": n, "rating": r} for n, r in rows]}

if __name__ == "__main__":
    init_db()
    app.run()
