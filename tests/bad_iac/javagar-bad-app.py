"""
javagar-bad-app.py – Deliberately insecure Python code for SAST Validation Test 1.
Bandit and Semgrep must catch and block this file.
DO NOT deploy.
"""
import sqlite3
import pickle
import os

# ── BAD #1: Hardcoded secret (Bandit B105 / Semgrep detect-hardcoded-secret) ──
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # noqa – intentional

# ── BAD #2: SQL string concatenation (Bandit B608 / Semgrep sql-injection) ────
def get_user_bad(user_input):
    conn = sqlite3.connect("javagar.db")
    # Dangerous – user input injected directly into query
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"  # noqa
    return conn.execute(query).fetchall()

# ── BAD #3: Unsafe deserialization (Bandit B301 / Semgrep pickle) ─────────────
def load_data_bad(data_bytes):
    return pickle.loads(data_bytes)  # noqa – intentional

# ── BAD #4: OS command injection (Bandit B605) ────────────────────────────────
def run_cmd_bad(filename):
    os.system("cat " + filename)  # noqa – intentional
