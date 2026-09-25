# secure_demo.py
# Safer version for educational comparison.
import sqlite3
import hashlib
import secrets
import subprocess
import ast
import operator as op

DATABASE = "users.db"
_ALLOWED_OPERATORS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER, username TEXT, role TEXT)")
    cur.execute("DELETE FROM users")
    cur.execute("INSERT INTO users VALUES (?, ?, ?)", (1, "alice", "student"))
    cur.execute("INSERT INTO users VALUES (?, ?, ?)", (2, "bob", "admin"))
    conn.commit()
    conn.close()

def find_user(username):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    rows = cur.fetchall()
    conn.close()
    return rows

def safe_calculate(expression):
    node = ast.parse(expression, mode="eval").body
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = node.left.value if isinstance(node.left, ast.Constant) else None
        right = node.right.value if isinstance(node.right, ast.Constant) else None
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return _ALLOWED_OPERATORS[type(node.op)](left, right)
    raise ValueError("Only simple arithmetic expressions are allowed")

def run_diagnostic(host):
    allowed_hosts = {"127.0.0.1", "localhost"}
    if host not in allowed_hosts:
        raise ValueError("Host is not allowed")
    return subprocess.run(["ping", "-c", "1", host], check=False, capture_output=True, text=True)

def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200000)
    return salt.hex() + ":" + digest.hex()

def generate_token():
    return secrets.token_urlsafe(32)

if __name__ == "__main__":
    init_db()
    print(find_user("alice"))
    print(safe_calculate("2 + 2"))
    print("Token:", generate_token())
