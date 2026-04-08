#!/usr/bin/env python3
"""
questions.py — Handles GET /questions.py and POST /questions.py

GET  → returns {"questions": [{"question": "...", "options": [...]}]}
POST → saves answers + hobbies to users.csv (final step of registration)
       body: {"username":..., "hobbies":[...], "answers":{0: "...", 1: "..."}, ...}
       cookie: session_token=<token>  (or username passed directly for demo mode)
"""

import json
import csv
from pathlib import Path
from signup import get_session_user, _load_users, _save_users

QUESTIONS_CSV = Path("questions.csv")


# ── Read questions.csv ─────────────────────────────────────────────────────────

def load_questions() -> list[dict]:
    """
    Parse questions.csv.

    Expected format:
        question,option1,option2,option3,option4
        How do you spend evenings?,Reading,Movies,Going out,Gaming

    Any number of option columns (option1..optionN).
    Extra empty cells are ignored.
    """
    if not QUESTIONS_CSV.exists():
        return _default_questions()

    with open(QUESTIONS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        questions = []
        for row in reader:
            q_text = row.get("question", "").strip()
            if not q_text:
                continue
            options = [
                v.strip()
                for k, v in row.items()
                if k.lower().startswith("option") and v.strip()
            ]
            if options:
                questions.append({"question": q_text, "options": options})
    return questions if questions else _default_questions()


def _default_questions() -> list[dict]:
    return [
        {
            "question": "How do you prefer to spend your evenings?",
            "options": ["Reading a book", "Watching movies", "Going out with friends", "Playing video games"],
        },
        {
            "question": "What kind of music do you enjoy most?",
            "options": ["Pop", "Rock / Metal", "Electronic / DJ", "Classical / Jazz"],
        },
        {
            "question": "How active are you on a typical day?",
            "options": [
                "Very active – gym or sport daily",
                "Moderately active – walks & stretches",
                "Mostly sedentary – office work",
                "It varies a lot",
            ],
        },
    ]


# ── Finalize user profile ──────────────────────────────────────────────────────

def finalize_profile(username: str, hobbies: list[str], answers: dict) -> bool:
    """
    Write hobbies and answers to the user's row in users.csv.
    Hobbies → pipe-separated string.
    Answers → JSON string.
    Returns True on success.
    """
    users = _load_users()
    found = False
    for user in users:
        if user["username"].lower() == username.lower():
            user["hobbies"] = "|".join(hobbies) if hobbies else ""
            user["answers"] = json.dumps(answers)
            found = True
            break
    if found:
        _save_users(users)
    return found


# ── Request handler ────────────────────────────────────────────────────────────

def handle_request(method: str, body_bytes: bytes, cookie_header: str = "") -> dict:
    if method == "GET":
        return {"questions": load_questions()}

    if method == "POST":
        try:
            body = json.loads(body_bytes)
        except Exception:
            return {"ok": False, "error": "Invalid JSON."}

        # Auth: prefer session cookie, fall back to username in body (demo)
        token = _extract_token(cookie_header)
        username = get_session_user(token) if token else body.get("username", "").strip()

        if not username:
            return {"ok": False, "error": "Not authenticated."}

        hobbies = body.get("hobbies", [])
        answers = body.get("answers", {})

        ok = finalize_profile(username, hobbies, answers)
        if ok:
            return {"ok": True, "redirect": "dashboard"}
        return {"ok": False, "error": "User not found."}

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
    qs = load_questions()
    for i, q in enumerate(qs, 1):
        print(f"Q{i}: {q['question']}")
        for opt in q["options"]:
            print(f"   • {opt}")
