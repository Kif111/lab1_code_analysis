"""Tests for authentication, sessions and access control in the grades portal.

Run against the fixed version (default):    pytest -v test_grades.py
Run against the original version:           APP_MODULE=grades_app pytest -v test_grades.py
"""
import importlib
import os
import re

import pytest

app_module = importlib.import_module(os.environ.get("APP_MODULE", "grades_app_fixed"))
HTTPS = "https://localhost"  # the fixed cookie is sent only over HTTPS, as in production


@pytest.fixture
def client():
    getattr(app_module, "FAILURES", {}).clear()
    return app_module.app.test_client()


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, base_url=HTTPS)


def get(client, url):
    return client.get(url, base_url=HTTPS)


def test_login_with_correct_password(client):
    assert login(client, "aigerim", "Spring-2026!").status_code == 200


def test_not_logged_in_gets_401(client):
    assert get(client, "/grades/1").status_code == 401


# 1. Passwords are stored as slow, salted hashes
def test_passwords_are_not_plain_sha256():
    stored = app_module.USERS["aigerim"]["password"]
    assert not re.fullmatch(r"[0-9a-f]{64}", stored)
    assert stored.startswith(("scrypt:", "pbkdf2:"))


# 2. The answer does not reveal whether a user name exists
def test_same_answer_for_unknown_user_and_wrong_password(client):
    unknown = login(client, "nobody", "whatever")
    wrong = login(client, "aigerim", "wrong-password")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.get_json() == wrong.get_json()


# 3. Failed attempts are limited
def test_account_locked_after_five_failures(client):
    for _ in range(5):
        login(client, "daniyar", "wrong-password")
    assert login(client, "daniyar", "Autumn-2026!").status_code == 429


# 4. A student sees only their own grades
def test_student_sees_own_grades(client):
    login(client, "aigerim", "Spring-2026!")
    assert get(client, "/grades/1").status_code == 200


def test_student_cannot_see_other_students_grades(client):
    login(client, "aigerim", "Spring-2026!")
    assert get(client, "/grades/2").status_code == 403


def test_teacher_sees_any_grades(client):
    login(client, "teacher", "Teach-PCAO-3307")
    assert get(client, "/grades/2").status_code == 200


# 5. Only a teacher may change grades
def test_student_cannot_set_grade(client):
    login(client, "aigerim", "Spring-2026!")
    resp = client.post("/grades/1", data={"course": "PCAO 3307", "grade": "100"}, base_url=HTTPS)
    assert resp.status_code == 403
    assert app_module.GRADES[1]["PCAO 3307"] == 92


def test_teacher_can_set_grade(client):
    login(client, "teacher", "Teach-PCAO-3307")
    resp = client.post("/grades/2", data={"course": "PCAO 3307", "grade": "81"}, base_url=HTTPS)
    assert resp.status_code == 200


# 6. Logout ends the session
def test_logout_ends_session(client):
    login(client, "aigerim", "Spring-2026!")
    client.post("/logout", base_url=HTTPS)
    assert get(client, "/grades/1").status_code == 401


# 7. The session cookie is protected
def test_session_cookie_flags(client):
    cookie = login(client, "aigerim", "Spring-2026!").headers.get("Set-Cookie", "")
    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
