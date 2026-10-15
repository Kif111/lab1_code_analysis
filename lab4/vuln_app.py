import hashlib
import os
import pickle
import sqlite3
import subprocess

from flask import Flask, request

app = Flask(__name__)
SECRET_KEY = "admin123"

def get_db():
    return sqlite3.connect("users.db")

@app.route("/user")
def user():
    name = request.args.get("name", "")
    conn = get_db()
    # Fix 2: parameterized query
    return str(conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall())

@app.route("/ping")
def ping():
    host = request.args.get("host")
    out = subprocess.check_output("ping -c 1 " + host, shell=True)
    return out

@app.route("/load", methods=["POST"])
def load():
    data = pickle.loads(request.data)
    return str(data)

@app.route("/hash")
def hash_password():
    pwd = request.args.get("pwd", "")
    # Fix 5: scrypt instead of MD5, with salt
    salt = os.urandom(16)
    return hashlib.scrypt(pwd.encode(), salt=salt, n=2**14, r=8, p=1).hex()

@app.route("/file")
def read_file():
    # Fix 6: strip directory part
    fname = os.path.basename(request.args.get("f", ""))
    with open(os.path.join("files", fname)) as fh:
        return fh.read()

if __name__ == "__main__":
    app.run(debug=True)
