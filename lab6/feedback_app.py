"""feedback_app.py - students leave feedback on a course: name, e-mail, rating 1-5, comment."""
import logging
import sqlite3

from flask import Flask, request

app = Flask(__name__)
log = logging.getLogger("feedback")
log.setLevel(logging.INFO)
_handler = logging.FileHandler("feedback.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
log.addHandler(_handler)

DB = "feedback.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS feedback (name TEXT, email TEXT, rating INTEGER, comment TEXT)")

@app.route("/feedback", methods=['POST'])
def add_feedback():
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    rating = int(request.form.get("rating", ""))
    comment = request.form.get("comment", "")

    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO feedback VALUES (?, ?, ?, ?)", (name, email, rating, comment))

    log.info("feedback from %s: %s", name, comment)
    return f'<p>Thank you, {name}! Your rating: {rating}</p>'

@app.route("/feedback")
def list_feedback():
    sort = request.args.get("sort", "rating")
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(f"SELECT name, rating FROM feedback ORDER BY {sort}").fetchall()
    return {"feedback": [{"name": n, "rating": r} for n, r in rows]}

if __name__ == "__main__":
    init_db()
    app.run()
