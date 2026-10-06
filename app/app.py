"""
DevSecOps Demo Application – javagar
A minimal Flask app used to demonstrate SAST scanning with Bandit and Semgrep.
"""
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# ------------------------------------------------------------------
# GOOD path – parameterized query, no secrets
# ------------------------------------------------------------------
DATABASE = "javagar.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Return a user by ID (safe parameterized query)."""
    conn = get_db()
    row = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "not found"}), 404


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(
        host=os.environ.get("APP_HOST", "0.0.0.0"),  # nosec B104
        port=int(os.environ.get("APP_PORT", 8080)),
    )
