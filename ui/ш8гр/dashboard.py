"""
dashboard.py — страница профиля авторизованного пользователя.

Читает профиль из sessionStorage["draft_user"] (только что зарегистрировался/
вошёл) или из localStorage["session"] + localStorage["user:<username>"]
(вернулся позже).

Кнопка log out очищает сессию и редиректит на signup.html.
"""

import json
from js import document, window, localStorage
from pyodide.ffi import create_proxy

# ── загрузка профиля ──────────────────────────────────────

def _load_profile() -> dict | None:
    # 1) только что залогинились / зарегистрировались
    raw = window.sessionStorage.getItem("draft_user")
    if raw:
        return json.loads(raw)

    # 2) вернулись позже — берём из localStorage сессию
    username = localStorage.getItem("session")
    if not username:
        return None

    stored = localStorage.getItem(f"user:{username.lower()}")
    if not stored:
        return None

    user = json.loads(stored)
    # answers хранятся как {str: str}, ключи — строки
    if isinstance(user.get("answers"), str):
        try:
            user["answers"] = json.loads(user["answers"])
        except Exception:
            user["answers"] = {}
    return user

# ── рендер ────────────────────────────────────────────────

def render(user: dict) -> None:
    name     = user.get("name") or user.get("username") or "?"
    username = user.get("username", "")
    age      = user.get("age", "")
    hobbies  = user.get("hobbies") or []
    answers  = user.get("answers") or {}

    # аватар — первые 2 буквы имени
    initials = "".join(w[0] for w in name.split() if w).upper()[:2] or "?"
    document.getElementById("p-avatar").textContent = initials
    document.getElementById("p-name").textContent   = name
    document.getElementById("p-meta").textContent   = (
        f"@{username}" + (f"  ·  age {age}" if age else "")
    )

    # хобби-теги
    hobbies_el = document.getElementById("p-hobbies")
    hobbies_el.innerHTML = ""
    if hobbies:
        for h in hobbies:
            tag = document.createElement("span")
            tag.className   = "hobby-tag"
            tag.textContent = h
            hobbies_el.appendChild(tag)
    else:
        hobbies_el.innerHTML = (
            '<span style="font-size:11px;color:var(--dimmed)">No hobbies selected</span>'
        )

    # ответы
    answers_el = document.getElementById("p-answers")
    answers_el.innerHTML = ""
    if answers:
        for i, v in sorted(answers.items(), key=lambda x: int(x[0])):
            row = document.createElement("div")
            row.className = "profile-answer-row"

            label = document.createElement("span")
            label.className   = "answer-label"
            label.textContent = f"Q{int(i) + 1}"

            val = document.createElement("span")
            val.className   = "answer-value"
            val.textContent = v

            row.appendChild(label)
            row.appendChild(val)
            answers_el.appendChild(row)

# ── logout ─────────────────────────────────────────────────

def on_logout(event=None):
    localStorage.removeItem("session")
    window.sessionStorage.removeItem("draft_user")
    window.location.href = "signup.html"

# ── инициализация ──────────────────────────────────────────

user = _load_profile()
if user:
    render(user)
else:
    window.location.href = "signup.html"

document.getElementById("btn-logout").addEventListener("click", create_proxy(on_logout))