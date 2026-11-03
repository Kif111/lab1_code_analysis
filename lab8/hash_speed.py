"""hash_speed.py - how many password hashes per second can this computer compute?"""
import hashlib
import time
from werkzeug.security import generate_password_hash

def rate(function, seconds=1.0):
    count, start = 0, time.perf_counter()
    while time.perf_counter() - start < seconds:
        function(f"candidate-{count}")
        count += 1
    return count / (time.perf_counter() - start)

sha = rate(lambda pw: hashlib.sha256(pw.encode()).hexdigest())
scrypt = rate(lambda pw: generate_password_hash(pw))

print(f"SHA-256: {sha:12,.0f} hashes per second")
print(f"scrypt:  {scrypt:12,.1f} hashes per second")
print(f"scrypt is about {sha / scrypt:,.0f} times slower per guess")
