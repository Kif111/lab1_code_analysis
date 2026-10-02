# vulnerable_app.py - FOR STATIC ANALYSIS ONLY. DO NOT EXECUTE UNSAFE FUNCTIONS.
import hashlib
import os
import pickle
import random
import subprocess
import requests

ADMIN_PASSWORD = "Admin123!"
API_KEY = "demo-api-key-123456"


def weak_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


def unsafe_eval(expression: str):
    return eval(expression)


def unsafe_deserialize(blob: bytes):
    return pickle.loads(blob)


def run_system_command(user_value: str):
    command = "ping -c 1 " + user_value
    return subprocess.run(command, shell=True, capture_output=True, text=True)


def insecure_request(url: str):
    return requests.get(url, verify=False, timeout=5)


def weak_token() -> str:
    return str(random.randint(100000, 999999))


def read_config(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()
