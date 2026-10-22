"""Your boundary-value tests for the feedback service (Lab 6, Task 3).

Run against the original version: pytest -v test_feedback_mine.py
Run against your fixed version: APP_MODULE=feedback_app_fixed pytest -v test_feedback_mine.py
"""
import importlib
import os
import tempfile
from pathlib import Path

WORK = Path(tempfile.mkdtemp())
os.chdir(WORK)
app_module = importlib.import_module(os.environ.get("APP_MODULE", "feedback_app"))
app_module.init_db()
client = app_module.app.test_client()

GOOD = {"name": "Aigerim", "email": "student@enu.kz", "rating": "5", "comment": "Clear lecture"}

def post(**changes):
    return client.post("/feedback", data={**GOOD, **changes})

def log_lines():
    return (WORK / "feedback.log").read_text(encoding="utf-8").splitlines()

# Example 1: valid input must be accepted
def test_valid_feedback_is_accepted():
    assert post().status_code == 200

# Example 2: a value just outside the valid range must be rejected with 400
def test_rating_zero_is_rejected():
    assert post(rating="0").status_code == 400

# TODO: add your own tests below, at least one for each field and for the sort parameter.

# ============ MY BOUNDARY VALUE TESTS ============

# --- rating ---
def test_rating_negative_is_rejected():
    assert post(rating="-1").status_code == 400

def test_rating_six_is_rejected():
    assert post(rating="6").status_code == 400

def test_rating_non_numeric_rejected_no_500():
    assert post(rating="five").status_code == 400

def test_rating_empty_rejected_no_500():
    assert post(rating="").status_code == 400

def test_rating_one_accepted():
    assert post(rating="1").status_code == 200

# --- name ---
def test_name_empty_rejected():
    assert post(name="").status_code == 400

def test_name_too_long_rejected():
    assert post(name="A" * 101).status_code == 400

def test_name_is_html_escaped():
    resp = post(name="Tom & Jerry <Admin>")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Должно быть экранировано: &amp; и &lt; &gt;
    assert "Tom &amp; Jerry &lt;Admin&gt;" in body
    assert "<Admin>" not in body

# --- email ---
def test_email_invalid_rejected():
    assert post(email="not-an-email").status_code == 400

def test_email_empty_rejected():
    assert post(email="").status_code == 400

# --- comment ---
def test_comment_max_length_accepted():
    assert post(comment="a" * 1000).status_code == 200

def test_comment_too_long_rejected():
    assert post(comment="a" * 1001).status_code == 400

def test_comment_newline_logged_as_one_line():
    before = len(log_lines())
    post(comment="line1\nline2\nline3")
    after = len(log_lines())
    # В лог должна добавиться ровно одна строка, а не три
    assert after - before == 1

# --- sort ---
def test_sort_rating_accepted():
    assert client.get("/feedback", query_string={"sort": "rating"}).status_code == 200

def test_sort_name_accepted():
    assert client.get("/feedback", query_string={"sort": "name"}).status_code == 200

def test_sort_unknown_no_500():
    assert client.get("/feedback", query_string={"sort": "unknown"}).status_code in (200, 400)

# --- Additional tests for Task 6 ---
def test_kazakh_name_accepted():
    assert post(name="Айгүл").status_code == 200

def test_whitespace_only_name_rejected():
    assert post(name="   ").status_code == 400

# --- Additional tests for Task 6 ---
def test_kazakh_name_accepted():
    assert post(name="Айгүл").status_code == 200

def test_whitespace_only_name_rejected():
    assert post(name="   ").status_code == 400
