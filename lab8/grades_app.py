"""grades_app.py - a small grades portal: students see their grades, teachers set grades."""
import hashlib
import os

from flask import Flask, abort, request, session

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

USERS = {
    "aigerim": {"id": 1, "role": "student", "password": hash_password("Spring-2026")},
    "daniyar": {"id": 2, "role": "student", "password": hash_password("Autumn-2026")},
    "teacher": {"id": 100, "role": "teacher", "password": hash_password("Teach-PCAO-3307")},
}
GRADES = {1: {"PCAO 3307": 92}, 2: {"PCAO 3307": 78}}

@app.post("/login")
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    user = USERS.get(username)
    if user is None:
        return {"error": "unknown user"}, 401
    if user["password"] != hash_password(password):
        return {"error": "wrong password"}, 401
    session["user"] = username
    return {"ok": True}

@app.get("/grades/<int:student_id>")
def get_grades(student_id):
    if "user" not in session:
        abort(401)
    return {"student_id": student_id, "grades": GRADES.get(student_id, {})}

@app.post("/grades/<int:student_id>")
def set_grade(student_id):
    if "user" not in session:
        abort(401)
    GRADES.setdefault(student_id, {})[request.form["course"]] = int(request.form["grade"])
    return {"ok": True}

@app.post("/logout")
def logout():
    return {"ok": True}

if __name__ == "__main__":
    app.run()
