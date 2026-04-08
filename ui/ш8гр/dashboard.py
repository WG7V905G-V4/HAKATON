#!/usr/bin/env python3
"""
dashboard.py — Handles GET /dashboard.py

GET → returns the currently logged-in user's profile
      Reads session_token from Cookie header, looks up users.csv.
      Returns {"ok": True, "user": {...}} or {"ok": False, "error": "..."}

Also handles POST /dashboard.py for logout:
POST {"action": "logout"} → deletes session, returns {"ok": True}
"""

import json
from pathlib import Path
from signup import get_session_user, delete_session, _load_users


def get_user_profile(username: str) -> dict | None:
    """Load and return the full user profile dict, or None if not found."""
    users = _load_users()
    for user in users:
        if user["username"].lower() == username.lower():
            hobbies = [h for h in user.get("hobbies", "").split("|") if h]
            try:
                answers = json.loads(user.get("answers", "{}") or "{}")
            except json.JSONDecodeError:
                answers = {}
            return {
                "name":     user.get("name", ""),
                "username": user.get("username", ""),
                "age":      user.get("age", ""),
                "hobbies":  hobbies,
                "answers":  answers,
            }
    return None


def handle_request(method: str, body_bytes: bytes, cookie_header: str = "") -> dict:
    token = _extract_token(cookie_header)

    if not token:
        return {"ok": False, "error": "No session. Please log in.", "redirect": "signup"}

    username = get_session_user(token)
    if not username:
        return {"ok": False, "error": "Session expired. Please log in.", "redirect": "signup"}

    if method == "GET":
        profile = get_user_profile(username)
        if not profile:
            return {"ok": False, "error": "User not found."}
        return {"ok": True, "user": profile}

    if method == "POST":
        try:
            body = json.loads(body_bytes)
        except Exception:
            return {"ok": False, "error": "Invalid JSON."}

        if body.get("action") == "logout":
            delete_session(token)
            return {"ok": True, "redirect": "signup"}

        return {"ok": False, "error": "Unknown action."}

    return {"ok": False, "error": "Method not allowed."}


def _extract_token(cookie_header: str) -> str | None:
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == "session_token":
            return v.strip()
    return None


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    # Usage: python dashboard.py <token>
    token = sys.argv[1] if len(sys.argv) > 1 else ""
    cookie = f"session_token={token}"
    result = handle_request("GET", b"", cookie)
    print(json.dumps(result, ensure_ascii=False, indent=2))
