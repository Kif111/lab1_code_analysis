# remediated_app.py - safer alternatives for the lab
import hashlib
import json
import os
import secrets
import subprocess
import requests

API_KEY = os.environ.get("LAB_API_KEY")


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json(text: str):
    return json.loads(text)


def run_ping(host: str):
    return subprocess.run(
        ["ping", "-c", "1", host],
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )


def secure_request(url: str):
    return requests.get(url, verify=True, timeout=5)


def strong_token() -> str:
    return secrets.token_urlsafe(24)
