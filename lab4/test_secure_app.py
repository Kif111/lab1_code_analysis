"""Tests that prove each fix in secure_app.py. Run with: pytest -v"""
import os
import sqlite3
import tempfile
from pathlib import Path

# Test environment: set before the application is imported
WORK = Path(tempfile.mkdtemp())
(WORK / "files").mkdir()
(WORK / "files" / "report.txt").write_text("quarterly report")
os.environ["SECRET_KEY"] = "test-secret-from-environment"
os.environ["DB_PATH"] = str(WORK / "users.db")
os.environ["FILES_DIR"] = str(WORK / "files")
os.environ.pop("FLASK_DEBUG", None)

with sqlite3.connect(os.environ["DB_PATH"]) as conn:
    conn.execute("CREATE TABLE users (name TEXT)")
    conn.executemany("INSERT INTO users VALUES (?)", [("Alice",), ("O'Brien",)])

import secure_app  # noqa: E402

client = secure_app.app.test_client()


# 1. Secret comes from the environment
def test_secret_key_from_environment():
    assert secure_app.app.config["SECRET_KEY"] == "test-secret-from-environment"


# 2. Parameterized query: a legitimate name with an apostrophe works
def test_user_lookup_with_apostrophe():
    resp = client.get("/user", query_string={"name": "O'Brien"})
    assert resp.status_code == 200
    assert resp.get_json() == {"users": ["O'Brien"]}


def test_unknown_user_returns_empty_list():
    resp = client.get("/user", query_string={"name": "Nobody"})
    assert resp.get_json() == {"users": []}


# 3. Host names are checked against an allow-list before ping runs
def test_valid_host_names_accepted():
    assert secure_app.is_valid_host("example.com")
    assert secure_app.is_valid_host("10.0.0.1")


def test_invalid_host_names_rejected():
    assert not secure_app.is_valid_host("")
    assert not secure_app.is_valid_host("two words")
    assert not secure_app.is_valid_host("-c")


def test_ping_rejects_invalid_host_with_400():
    resp = client.get("/ping", query_string={"host": "two words"})
    assert resp.status_code == 400


# 4. Only JSON is accepted, never pickle
def test_load_accepts_json():
    resp = client.post("/load", data='{"course": "PCAO 3307"}')
    assert resp.status_code == 200
    assert resp.get_json() == {"received": {"course": "PCAO 3307"}}


def test_load_rejects_non_json_with_400():
    resp = client.post("/load", data=b'\x80\x04not json')
    assert resp.status_code == 400


# 5. Passwords are salted and slow-hashed
def test_same_password_gives_different_hashes():
    assert secure_app.hash_password("Secret-123") != secure_app.hash_password("Secret-123")


def test_verify_password():
    stored = secure_app.hash_password("Secret-123")
    assert secure_app.verify_password("Secret-123", stored)
    assert not secure_app.verify_password("wrong", stored)


def test_hash_route_uses_post():
    assert client.get("/hash").status_code == 405
    assert "$" in client.post("/hash", data={"pwd": "Secret-123"}).get_json()["hash"]


# 6. Files are served only from FILES_DIR
def test_file_inside_folder_is_served():
    resp = client.get("/file", query_string={"f": "report.txt"})
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "quarterly report"


def test_directory_part_is_dropped():
    assert secure_app.safe_path("sub/report.txt") == secure_app.FILES_DIR / "report.txt"


def test_empty_name_rejected():
    assert client.get("/file", query_string={"f": ""}).status_code == 400


def test_missing_file_returns_404():
    assert client.get("/file", query_string={"f": "missing.txt"}).status_code == 404


# 7. Debug mode is off by default
def test_debug_off_by_default():
    assert secure_app.debug_enabled() is False
