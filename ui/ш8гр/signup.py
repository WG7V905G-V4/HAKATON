#!/usr/bin/env python3
"""
signup.py — Handles POST /signup.py
Modes:
  signup → validate unique username, hash password, write to users.csv
  login  → verify credentials, set session cookie

Run with: python server.py  (see server.py)
This module is imported by the HTTP server.
"""

import json
import csv
import hashlib
import os
import http.cookies
import secrets
from pathlib import Path

USERS_CSV = Path("users.csv")
SESSIONS_FILE = Path("sessions.json")

FIELDNAMES = ["name", "username", "age", "password_hash", "hobbies", "answers"]


# ── CSV helpers ────────────────────────────────────────────────────────────────

def _load_users() -> list[dict]:
    if not USERS_CSV.exists():
        return []
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _save_users(users: list[dict]) -> None:
    with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(users)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Session helpers ────────────────────────────────────────────────────────────

def _load_sessions() -> dict:
    if not SESSIONS_FILE.exists():
        return {}
    with open(SESSIONS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_sessions(sessions: dict) -> None:
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f)


def create_session(username: str) -> str:
    """Create a session token for the user. Returns the token."""
    token = secrets.token_hex(32)
    sessions = _load_sessions()
    sessions[token] = username
    _save_sessions(sessions)
    return token


def get_session_user(token: str) -> str | None:
    """Return username for token, or None if invalid."""
    sessions = _load_sessions()
    return sessions.get(token)


def delete_session(token: str) -> None:
    sessions = _load_sessions()
    sessions.pop(token, None)
    _save_sessions(sessions)


# ── Core logic ─────────────────────────────────────────────────────────────────

def handle_signup(body: dict) -> dict:
    """
    Register a new user.
    Returns {"ok": True, "user": {...}, "redirect": "hobbies"} or {"ok": False, "error": "..."}
    """
    name = (body.get("name") or "").strip()
    username = (body.get("username") or "").strip()
    age = str(body.get("age") or "").strip()
    password = body.get("password") or ""

    if not all([name, username, age, password]):
        return {"ok": False, "error": "All fields are required."}

    if not username.isalnum():
        return {"ok": False, "error": "Username must contain only letters and numbers."}

    users = _load_users()

    # Check uniqueness
    if any(u["username"].lower() == username.lower() for u in users):
        return {"ok": False, "error": "This username is already taken."}

    # Create user record (hobbies/answers filled in later pages)
    new_user = {
        "name": name,
        "username": username,
        "age": age,
        "password_hash": _hash_password(password),
        "hobbies": "",
        "answers": "",
    }
    users.append(new_user)
    _save_users(users)

    token = create_session(username)

    return {
        "ok": True,
        "redirect": "hobbies",
        "session_token": token,
        "user": {"name": name, "username": username, "age": age},
    }


def handle_login(body: dict) -> dict:
    """
    Authenticate existing user.
    Returns {"ok": True, "user": {...}, "redirect": "dashboard"} or {"ok": False, "error": "..."}
    """
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    if not username or not password:
        return {"ok": False, "error": "Username and password are required."}

    users = _load_users()
    match = next((u for u in users if u["username"].lower() == username.lower()), None)

    if not match or match["password_hash"] != _hash_password(password):
        return {"ok": False, "error": "Invalid username or password."}

    token = create_session(match["username"])

    # Parse stored hobbies/answers
    hobbies = [h for h in match.get("hobbies", "").split("|") if h]
    try:
        answers = json.loads(match.get("answers", "{}") or "{}")
    except json.JSONDecodeError:
        answers = {}

    return {
        "ok": True,
        "redirect": "dashboard",
        "session_token": token,
        "user": {
            "name": match["name"],
            "username": match["username"],
            "age": match["age"],
            "hobbies": hobbies,
            "answers": answers,
        },
    }


# ── WSGI-style handler (used by server.py) ────────────────────────────────────

def handle_request(method: str, body_bytes: bytes, cookie_header: str = "") -> tuple[dict, str]:
    """
    Returns (response_dict, session_token_or_empty_string).
    server.py sets the Set-Cookie header if token is non-empty.
    """
    if method != "POST":
        return {"ok": False, "error": "Method not allowed."}, ""

    try:
        body = json.loads(body_bytes)
    except Exception:
        return {"ok": False, "error": "Invalid JSON."}, ""

    mode = body.get("mode")
    if mode == "signup":
        result = handle_signup(body)
    elif mode == "login":
        result = handle_login(body)
    else:
        return {"ok": False, "error": "Unknown mode."}, ""

    token = result.pop("session_token", "")
    return result, token


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Quick smoke test
    print("=== Signup test ===")
    r, t = handle_request("POST", json.dumps({
        "mode": "signup", "name": "Alice", "username": "alice",
        "age": "25", "password": "secret"
    }).encode())
    print(r, "token:", t)

    print("\n=== Login test ===")
    r, t = handle_request("POST", json.dumps({
        "mode": "login", "username": "alice", "password": "secret"
    }).encode())
    print(r, "token:", t)

    print("\n=== Duplicate username ===")
    r, _ = handle_request("POST", json.dumps({
        "mode": "signup", "name": "Bob", "username": "alice",
        "age": "30", "password": "other"
    }).encode())
    print(r)
