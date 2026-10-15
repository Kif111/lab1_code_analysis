import hashlib
import hmac
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path

from flask import Flask, abort, request

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

DB_PATH = os.environ.get("DB_PATH", "users.db")
FILES_DIR = Path(os.environ.get("FILES_DIR", "files")).resolve()
HOST_RE = re.compile(r"[A-Za-z0-9.-]{1,253}")


def get_db():
    return sqlite3.connect(DB_PATH)


@app.route("/user")
def user():
    name = request.args.get("name", "")
    with get_db() as conn:
        rows = conn.execute("SELECT name FROM users WHERE name = ?", (name,)).fetchall()
    return {"users": [row[0] for row in rows]}


def is_valid_host(host):
    return bool(HOST_RE.fullmatch(host)) and not host.startswith("-")


@app.route("/ping")
def ping():
    host = request.args.get("host", "")
    if not is_valid_host(host):
        abort(400)
    result = subprocess.run(
        ["ping", "-c", "1", host],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return {"reachable": result.returncode == 0}


@app.route("/load", methods=["POST"])
def load():
    try:
        data = json.loads(request.get_data(as_text=True))
    except ValueError:
        abort(400)
    return {"received": data}


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + "$" + digest.hex()


def verify_password(password, stored):
    salt_hex, _ = stored.split("$")
    candidate = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, stored)


@app.route("/hash", methods=["POST"])
def hash_route():
    return {"hash": hash_password(request.form.get("pwd", ""))}


def safe_path(name):
    path = (FILES_DIR / Path(name).name).resolve()
    if path.parent != FILES_DIR:
        raise ValueError("path outside FILES_DIR")
    return path


@app.route("/file")
def read_file():
    try:
        path = safe_path(request.args.get("f", ""))
    except ValueError:
        abort(400)
    if not path.is_file():
        abort(404)
    return path.read_text()


def debug_enabled():
    return os.environ.get("FLASK_DEBUG") == "1"


if __name__ == "__main__":
    app.run(debug=debug_enabled())
