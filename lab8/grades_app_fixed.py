"""grades_app_fixed.py - the grades portal with authentication, sessions and access control fixed."""
import os
import time
from datetime import timedelta

from flask import Flask, abort, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or os.urandom(32),
    SESSION_COOKIE_SECURE=True,          # Fix 7: the cookie travels only over HTTPS,
    SESSION_COOKIE_HTTPONLY=True,        # is invisible to page scripts,
    SESSION_COOKIE_SAMESITE="Lax",       # is not sent with requests started by other sites,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),  # and expires after 30 minutes
)

MAX_FAILURES, LOCK_SECONDS = 5, 15 * 60
FAILURES = {}  # username -> (number of failed attempts, time of the first failure)


def hash_password(password):
    # Fix 1: slow, salted hash (scrypt in Werkzeug 3); the salt is stored inside the result
    return generate_password_hash(password)


USERS = {
    "aigerim": {"id": 1, "role": "student", "password": hash_password("Spring-2026!")},
    "daniyar": {"id": 2, "role": "student", "password": hash_password("Autumn-2026!")},
    "teacher": {"id": 100, "role": "teacher", "password": hash_password("Teach-PCAO-3307")},
}
GRADES = {1: {"PCAO 3307": 92}, 2: {"PCAO 3307": 78}}
DUMMY_HASH = hash_password("not-a-real-password")


def locked(username):
    count, first = FAILURES.get(username, (0, 0.0))
    if time.monotonic() - first > LOCK_SECONDS:
        FAILURES.pop(username, None)
        return False
    return count >= MAX_FAILURES


def record_failure(username):
    count, first = FAILURES.get(username, (0, time.monotonic()))
    FAILURES[username] = (count + 1, first)


@app.post("/login")
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if locked(username):                 # Fix 3: limit failed attempts per account
        return {"error": "too many attempts, try again later"}, 429
    user = USERS.get(username)
    # Fix 1: constant-time comparison; an unknown user costs the same time as a known one
    ok = check_password_hash(user["password"] if user else DUMMY_HASH, password)
    if not (user and ok):
        record_failure(username)
        return {"error": "invalid username or password"}, 401  # Fix 2: one message for both cases
    FAILURES.pop(username, None)
    session.clear()                      # start a fresh session at every login
    session["user"] = username
    session.permanent = True
    return {"ok": True}


def current_user():
    username = session.get("user")
    if username not in USERS:
        abort(401)
    return USERS[username]


@app.get("/grades/<int:student_id>")
def get_grades(student_id):
    user = current_user()
    # Fix 4: a student may see only their own grades; a teacher may see all
    if user["role"] != "teacher" and user["id"] != student_id:
        abort(403)
    return {"student_id": student_id, "grades": GRADES.get(student_id, {})}


@app.post("/grades/<int:student_id>")
def set_grade(student_id):
    user = current_user()
    if user["role"] != "teacher":        # Fix 5: only teachers may change grades
        abort(403)
    course = request.form.get("course", "").strip()
    grade = request.form.get("grade", "")
    if not course or not grade.isdigit() or not 0 <= int(grade) <= 100:
        abort(400)
    GRADES.setdefault(student_id, {})[course] = int(grade)
    return {"ok": True}


@app.post("/logout")
def logout():
    session.clear()                      # Fix 6: logout really ends the session
    return {"ok": True}


if __name__ == "__main__":
    app.run()
