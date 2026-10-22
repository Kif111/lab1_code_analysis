"""Tests for the feedback service. Each test states how one input must be handled.

Run against the fixed version (default):     pytest -v test_feedback.py
Run against the original version:            APP_MODULE=feedback_app pytest -v test_feedback.py
"""
import importlib
import os
import tempfile
from pathlib import Path

WORK = Path(tempfile.mkdtemp())
os.chdir(WORK)  # the database and the log are created in a fresh folder
app_module = importlib.import_module(os.environ.get("APP_MODULE", "feedback_app_fixed"))
app_module.init_db()
client = app_module.app.test_client()

GOOD = {"name": "Aigerim", "email": "student@enu.kz", "rating": "5", "comment": "Clear lecture"}


def post(**changes):
    return client.post("/feedback", data={**GOOD, **changes})


def log_lines():
    return (WORK / "feedback.log").read_text(encoding="utf-8").splitlines()


def test_valid_feedback_is_accepted():
    resp = post()
    assert resp.status_code == 200
    assert "Aigerim" in resp.get_data(as_text=True)


# 1. Rating must be in range 1-5
def test_rating_out_of_range_is_rejected():
    assert post(rating="0").status_code == 400
    assert post(rating="6").status_code == 400


# 2. A rating that is not a number is a client error (400), not a crash (500)
def test_rating_not_a_number_is_rejected():
    assert post(rating="five").status_code == 400
    assert post(rating="").status_code == 400


# 3. User data is encoded before it is put into HTML
def test_name_is_html_encoded():
    body = post(name="Tom & Jerry <Admin>").get_data(as_text=True)
    assert "Tom &amp; Jerry &lt;Admin&gt;" in body
    assert "<Admin>" not in body


# 4. Only known columns can be used for sorting
def test_sort_by_known_column():
    assert client.get("/feedback", query_string={"sort": "name"}).status_code == 200


def test_sort_by_unknown_column_is_rejected():
    assert client.get("/feedback", query_string={"sort": "unknown"}).status_code == 400


# 5. One feedback adds exactly one line to the log
def test_line_break_in_comment_stays_in_one_log_line():
    before = len(log_lines())
    assert post(comment="first line\nsecond line").status_code == 200
    assert len(log_lines()) == before + 1


# 6. Field lengths are limited
def test_too_long_comment_is_rejected():
    assert post(comment="a" * 1001).status_code == 400
    assert post(comment="a" * 1000).status_code == 200


# 7. The e-mail address must have a valid format
def test_email_format_is_checked():
    assert post(email="not-an-email").status_code == 400
    assert post(email="aigerim.n@student.enu.kz").status_code == 200
