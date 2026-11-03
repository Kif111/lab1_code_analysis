"""grades_app_fixed.py - secure version of the grades portal."""
import os
from flask import Flask, abort, request, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32)

# Fix 7: Secure cookie flags
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Fix 1: Slow hashing (scrypt is default in werkzeug)
USERS = {
    "aigerim": {"id": 1, "role": "student", "password": generate_password_hash("Spring-2026")},
    "daniyar": {"id": 2, "role": "student", "password": generate_password_hash("Autumn-2026")},
    "teacher": {"id": 100, "role": "teacher", "password": generate_password_hash("Teach-PCAO-3307")},
}
GRADES = {1: {"PCAO 3307": 92}, 2: {"PCAO 3307": 78}}

# Fix 3: Track failed login attempts
FAILURES = {}
MAX_ATTEMPTS = 3

@app.post("/login")
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    
    # Fix 3: Check if blocked
    if FAILURES.get(username, 0) >= MAX_ATTEMPTS:
        return {"error": "Account temporarily locked"}, 403

    user = USERS.get(username)
    
    # Fix 2: Same message for unknown user or wrong password
    # Fix 1: Constant-time comparison via check_password_hash
    if user is None or not check_password_hash(user["password"], password):
        FAILURES[username] = FAILURES.get(username, 0) + 1
        return {"error": "Invalid username or password"}, 401

    # Successful login
    FAILURES[username] = 0  # Reset attempts
    session.clear()         # Fix 4: New session on login
    session["user"] = username
    return {"ok": True}

@app.get("/grades/<int:student_id>")
def get_grades(student_id):
    if "user" not in session:
        abort(401)
    
    current_user = USERS[session["user"]]
    
    # Fix 4: Authorization check
    # A student can only read their own grades.
    if current_user["role"] == "student" and current_user["id"] != student_id:
        abort(403)  # Forbidden
        
    return {"student_id": student_id, "grades": GRADES.get(student_id, {})}

@app.post("/grades/<int:student_id>")
def set_grade(student_id):
    if "user" not in session:
        abort(401)
        
    current_user = USERS[session["user"]]
    
    # Fix 5: Only teachers can set grades
    if current_user["role"] != "teacher":
        abort(403)
        
    GRADES.setdefault(student_id, {})[request.form["course"]] = int(request.form["grade"])
    return {"ok": True}

@app.post("/logout")
def logout():
    # Fix 6: Destroy session on logout
    session.clear()
    return {"ok": True}

if __name__ == "__main__":
    app.run()
