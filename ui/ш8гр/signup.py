"""
signup.py — логика страницы Sign up / Log in.

Хранилище: localStorage браузера.
Структура записи пользователя (JSON-строка под ключом "user:<username>"):
  {
    "name":     str,
    "username": str,
    "age":      str,
    "password": str,   # SHA-256 hex (через hashlib в Pyodide)
    "hobbies":  [],
    "answers":  {}
  }

Текущая сессия хранится под ключом "session" — просто username.
"""

import hashlib
import json
from js import document, window, localStorage

# ── утилиты ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _load_user(username: str) -> dict | None:
    raw = localStorage.getItem(f"user:{username.lower()}")
    return json.loads(raw) if raw else None

def _save_user(user: dict) -> None:
    localStorage.setItem(
        f"user:{user['username'].lower()}",
        json.dumps(user)
    )

def _set_session(username: str) -> None:
    localStorage.setItem("session", username.lower())

def _show_flash(msg: str, kind: str = "error") -> None:
    el = document.getElementById("flash")
    el.textContent = msg
    el.className   = f"flash {kind}"
    el.style.display = "block"

def _hide_flash() -> None:
    document.getElementById("flash").style.display = "none"

# ── режим (signup / login) ────────────────────────────────────────────────────

is_login = False

def toggle_mode(event=None):
    global is_login
    is_login = not is_login

    document.getElementById("heading-title").textContent = \
        "Log in" if is_login else "Sign up"
    document.getElementById("toggle-link").textContent = \
        "or sign up" if is_login else "or log in"
    document.getElementById("row-name").style.display = \
        "none" if is_login else ""
    document.getElementById("row-age").style.display  = \
        "none" if is_login else ""
    _hide_flash()

# ── submit ────────────────────────────────────────────────────────────────────

def handle_submit(event=None):
    _hide_flash()

    username = document.getElementById("inp-username").value.strip()
    password = document.getElementById("inp-password").value

    if not username or not password:
        _show_flash("Please fill in all required fields.")
        return

    if is_login:
        _do_login(username, password)
    else:
        _do_signup(username, password)

def _do_signup(username: str, password: str) -> None:
    name = document.getElementById("inp-name").value.strip()
    age  = document.getElementById("inp-age").value.strip()

    if not name or not age:
        _show_flash("Please fill in all fields.")
        return

    if not username.replace("_", "").isalnum():
        _show_flash("Username: letters, numbers and _ only.")
        return

    if _load_user(username):
        _show_flash("This username is already taken.")
        return

    user = {
        "name":     name,
        "username": username.lower(),
        "age":      age,
        "password": _hash(password),
        "hobbies":  [],
        "answers":  {}
    }
    _save_user(user)
    _set_session(username)

    # передаём черновик профиля в sessionStorage для следующих страниц
    window.sessionStorage.setItem("draft_user", json.dumps({
        "name":     name,
        "username": username.lower(),
        "age":      age,
        "hobbies":  [],
        "answers":  {}
    }))

    window.location.href = "hobbies.html"

def _do_login(username: str, password: str) -> None:
    user = _load_user(username)

    if not user or user["password"] != _hash(password):
        _show_flash("Invalid username or password.")
        return

    _set_session(username)
    window.sessionStorage.setItem("draft_user", json.dumps({
        "name":     user["name"],
        "username": user["username"],
        "age":      user["age"],
        "hobbies":  user.get("hobbies", []),
        "answers":  user.get("answers", {})
    }))
    window.location.href = "dashboard.html"

# ── wire up ───────────────────────────────────────────────────────────────────

document.getElementById("toggle-link").addEventListener("click",  toggle_mode)
document.getElementById("btn-continue").addEventListener("click", handle_submit)

# Enter key
def _on_keydown(event):
    if event.key == "Enter":
        handle_submit()

document.addEventListener("keydown", _on_keydown)