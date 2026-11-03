"""Your access-control tests for the grades portal (Lab 8, Task 2)."""
import importlib
import os
import pytest

app_module = importlib.import_module(os.environ.get("APP_MODULE", "grades_app"))
HTTPS = "https://localhost"

PASSWORDS = {"aigerim": "Spring-2026", "daniyar": "Autumn-2026", "teacher": "Teach-PCAO-3307"}

@pytest.fixture
def client():
    getattr(app_module, "FAILURES", {}).clear()
    return app_module.app.test_client()

def login(client, username, password=None):
    password = PASSWORDS.get(username, "") if password is None else password
    return client.post("/login", data={"username": username, "password": password}, base_url=HTTPS)

def get(client, url):
    return client.get(url, base_url=HTTPS)

def post(client, url, data=None):
    return client.post(url, data=data or {}, base_url=HTTPS)

# Example 1: anonymous users are refused
def test_anonymous_cannot_read_grades(client):
    assert get(client, "/grades/1").status_code == 401

# Example 2: a student can read their own grades
def test_student_reads_own_grades(client):
    login(client, "aigerim")
    assert get(client, "/grades/1").status_code == 200

# ============================================================
# MY ACCESS CONTROL & AUTHENTICATION TESTS
# ============================================================

# --- ACCESS CONTROL MATRIX ---
def test_teacher_reads_student_grades(client):
    login(client, "teacher")
    assert get(client, "/grades/1").status_code == 200

def test_student_cannot_read_other_grades(client):
    login(client, "aigerim")
    assert get(client, "/grades/2").status_code == 403  # Should be 403, code gives 200

def test_teacher_can_set_grades(client):
    login(client, "teacher")
    assert post(client, "/grades/1", {"course": "PCAO 3307", "grade": "100"}).status_code == 200

def test_student_cannot_set_grades(client):
    login(client, "aigerim")
    assert post(client, "/grades/1", {"course": "PCAO 3307", "grade": "100"}).status_code == 403  # Code gives 200

def test_anonymous_cannot_set_grades(client):
    assert post(client, "/grades/1", {"course": "PCAO 3307", "grade": "100"}).status_code == 401

# --- AUTHENTICATION CHECKLIST ---
def test_different_error_messages(client):
    resp_unknown = login(client, "unknown_user", "any_pass")
    resp_wrong = login(client, "aigerim", "wrong_pass")
    # Both should have the same generic message to prevent username enumeration
    assert resp_unknown.get_json() == resp_wrong.get_json()

def test_logout_clears_session(client):
    login(client, "aigerim")
    assert get(client, "/grades/1").status_code == 200
    post(client, "/logout")
    # After logout, session should be gone
    assert get(client, "/grades/1").status_code == 401

def test_secure_cookie_flags(client):
    resp = login(client, "aigerim")
    cookie_header = resp.headers.get("Set-Cookie", "")
    # Check for Secure, HttpOnly, SameSite flags
    assert "Secure" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite" in cookie_header

def test_slow_hashing(client):
    # Verify that the stored hash is long enough (scrypt hashes are much longer than sha256)
    stored_hash = app_module.USERS["aigerim"]["password"]
    assert len(stored_hash) > 64

# ============================================================
# ADDITIONAL TESTS FOR TASK 6
# ============================================================

def test_teacher_reads_after_student_logout(client):
    # Студент заходит и выходит
    login(client, "aigerim")
    post(client, "/logout")
    
    # Преподаватель заходит и читает оценки этого студента
    login(client, "teacher")
    assert get(client, "/grades/1").status_code == 200

def test_out_of_range_grade_rejected(client):
    login(client, "teacher")
    # Оценка 101 должна быть отклонена (400 Bad Request)
    assert post(client, "/grades/1", {"course": "PCAO 3307", "grade": "101"}).status_code == 400
    # Оценка -5 должна быть отклонена (400 Bad Request)
    assert post(client, "/grades/1", {"course": "PCAO 3307", "grade": "-5"}).status_code == 400
