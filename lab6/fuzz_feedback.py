"""fuzz_feedback.py - sends many random form values to the feedback service."""
import importlib
import os
import random
import sys
import tempfile
import time
from collections import Counter

module_name = sys.argv[1] if len(sys.argv) > 1 else "feedback_app"
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 500
rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 1)

sys.path.insert(0, os.getcwd())
os.chdir(tempfile.mkdtemp())

app_module = importlib.import_module(module_name)
app_module.init_db()
app_module.app.logger.disabled = True
client = app_module.app.test_client()

ALPHABET = "abcXYZ019 ,@-_&<>|\n" + "әткцөүіЖЄ"

def random_text(max_len=40):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, max_len)))

def random_form():
    form = {
        "name": random_text(),
        "email": rng.choice(["student@enu.kz", random_text()]),
        "rating": rng.choice(["1", "3", "5", "0", "6", "-1", "", "2.5", random_text(3)]),
        "comment": rng.choice(["ok", random_text(80), "a" * rng.randint(900, 1100)]),
    }
    for field in list(form):
        if rng.random() < 0.05:
            del form[field]
    return form

statuses, failures = Counter(), []
for i in range(runs):
    if rng.random() < 0.8:
        form = random_form()
        start = time.perf_counter()
        resp = client.post("/feedback", data=form)
        what = ("POST", form)
    else:
        sort = rng.choice(["rating", "name", random_text(8)])
        start = time.perf_counter()
        resp = client.get("/feedback", query_string={"sort": sort})
        what = ("GET sort", sort)

    elapsed = time.perf_counter() - start
    statuses[resp.status_code] += 1
    if resp.status_code not in (200, 400) or elapsed > 0.5:
        failures.append((resp.status_code, round(elapsed, 3), what))

print(f"{runs} requests to {module_name}: status codes {dict(sorted(statuses.items()))}")
print(f"rule violations: {len(failures)}")
for code, secs, what in failures[:5]:
    print(f"  status {code}, {secs} s: {what!r}")

sys.exit(1 if failures else 0)
