"""feedback_app_fixed.py - the feedback service with every input validated and every output encoded."""
import logging
import re
import sqlite3

from flask import Flask, abort, request
from markupsafe import escape

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # Fix 6a: limit the size of the whole request body
log = logging.getLogger("feedback")
log.setLevel(logging.INFO)
_handler = logging.FileHandler("feedback.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
log.addHandler(_handler)
DB = "feedback.db"

MAX_NAME, MAX_EMAIL, MAX_COMMENT = 100, 254, 1000
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,24}")
RATING_RE = re.compile(r"[1-5]")
SORT_COLUMNS = {"rating": "rating", "name": "name"}  # Fix 4: allow-list of column names


class InvalidInput(ValueError):
    """Raised when a field fails validation; the message names the field."""


def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS feedback (name TEXT, email TEXT, rating INTEGER, comment TEXT)")


def validate(form):
    name = form.get("name", "").strip()
    if not 1 <= len(name) <= MAX_NAME:                   # Fix 6b: length limits for every field
        raise InvalidInput("name")
    email = form.get("email", "").strip()
    if len(email) > MAX_EMAIL or not EMAIL_RE.fullmatch(email):  # Fix 7: format check, bounded
        raise InvalidInput("email")
    raw_rating = form.get("rating", "").strip()
    if not RATING_RE.fullmatch(raw_rating):              # Fix 1 and 2: only the digits 1-5 pass
        raise InvalidInput("rating")
    comment = form.get("comment", "")
    if len(comment) > MAX_COMMENT:
        raise InvalidInput("comment")
    return name, email, int(raw_rating), comment


def for_log(text):
    # Fix 5: line breaks in user data cannot start a new log entry
    return text.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")


@app.errorhandler(InvalidInput)
def invalid_input(err):
    return {"error": f"invalid field: {err}"}, 400


@app.route("/feedback", methods=["POST"])
def add_feedback():
    name, email, rating, comment = validate(request.form)
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO feedback VALUES (?, ?, ?, ?)", (name, email, rating, comment))
    log.info("feedback from %s: %s", for_log(name), for_log(comment))
    # Fix 3: encode user data for the HTML context
    return f"<p>Thank you, {escape(name)}! Your rating: {rating}</p>"


@app.route("/feedback")
def list_feedback():
    sort = request.args.get("sort", "rating")
    if sort not in SORT_COLUMNS:
        abort(400)
    with sqlite3.connect(DB) as conn:
        # the column name comes from the allow-list, never from the request
        rows = conn.execute(f"SELECT name, rating FROM feedback ORDER BY {SORT_COLUMNS[sort]}").fetchall()  # nosec B608
    return {"feedback": [{"name": n, "rating": r} for n, r in rows]}


if __name__ == "__main__":
    init_db()
    app.run()
