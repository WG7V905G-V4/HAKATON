#!/usr/bin/env python3
"""
hobbies.py — Handles GET /hobbies.py and POST /hobbies.py

GET  → returns {"hobbies": ["Photography", "Gaming", ...]} from hobbies.csv
POST → updates the logged-in user's hobbies field in users.csv
       body: {"hobbies": ["Gaming", "Reading"]}
       cookie: session_token=<token>
"""
from database.sql import *
import json
import csv
from pathlib import Path

from signup import get_session_user


# ── Read hobbies.csv ───────────────────────────────────────────────────────────

def load_hobbies() -> list[str]:
    """
    Parse hobbies.csv.
    Expected format — one column named 'hobby':
        hobby
        Photography
        Gaming
        ...
    Falls back to first column if 'hobby' header not found.
    """
    HOBBIES_CSV = Path("hobbies.csv")
    if not HOBBIES_CSV.exists():
        return _default_hobbies()

    with open(HOBBIES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        field = None
        hobbies = []
        for row in reader:
            if field is None:
                # Auto-detect column
                keys = [k.strip().lower() for k in row.keys()]
                field = list(row.keys())[keys.index("hobby")] if "hobby" in keys else list(row.keys())[0]
            val = row[field].strip()
            if val:
                hobbies.append(val)
        return hobbies if hobbies else _default_hobbies()


def _default_hobbies() -> list[str]:
    return [
        "Photography", "Cooking", "Gaming", "Reading", "Hiking",
        "Music", "Travel", "Painting", "Cycling", "Dancing",
        "Swimming", "Yoga", "Coding", "Gardening", "Chess",
        "Writing", "Fishing", "Surfing", "Climbing", "Pottery",
    ]


# ── Save hobbies to user record ────────────────────────────────────────────────

def save_user_hobbies(username: str, hobbies: list[str]):
    set_hobbies(mycursor, username, hobbies)


# ── Request handler ────────────────────────────────────────────────────────────

def handle_request(method: str, body_bytes: bytes, cookie_header: str = "") -> dict:
    if method == "GET":
        return {"hobbies": load_hobbies()}

    if method == "POST":
        # Authenticate
        token = _extract_token(cookie_header)
        username = get_session_user(token) if token else None
        if not username:
            return {"ok": False, "error": "Not authenticated."}

        try:
            body = json.loads(body_bytes)
        except Exception:
            return {"ok": False, "error": "Invalid JSON."}

        hobbies = body.get("hobbies", [])
        if not isinstance(hobbies, list):
            return {"ok": False, "error": "hobbies must be a list."}

        ok = save_user_hobbies(username, hobbies)
        return {"ok": ok, "error": None if ok else "User not found."}

    return {"ok": False, "error": "Method not allowed."}


def _extract_token(cookie_header: str) -> str | None:
    """Parse session_token from Cookie header string."""
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == "session_token":
            return v.strip()
    return None


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Hobbies:", load_hobbies())
