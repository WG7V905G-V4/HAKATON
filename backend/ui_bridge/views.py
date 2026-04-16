"""
ui_bridge/views.py

Серверная логика для signup / hobbies / questions / dashboard.
Использует SQLite (db.sqlite3 в папке backend) через прямой sqlite3 —
никаких импортов из ui/ (там PyScript-код для браузера).

Таблицы (уже созданы в db.sqlite3):
  users          — id, name, username, age, password, answers
  hobbies        — id, user_name, hobby
  sessions       — session_token, username, created_at
  activities     — id, title, author, tags, time_start, time_end, place, lat, lng, descr
  activity_users — id, activity_id, username
  friends        — id, username, username_friend
"""

import json
import uuid
import sqlite3
from pathlib import Path

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings


# ── БД ────────────────────────────────────────────────────────────────────────

def get_db():
    """Открывает соединение с db.sqlite3 из папки backend."""
    db_path = Path(settings.BASE_DIR) / "db.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row   # доступ к колонкам по имени
    return conn


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cookie_str(request) -> str:
    return request.META.get("HTTP_COOKIE", "")


def _extract_token(cookie_header: str) -> str | None:
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == "session_token":
            return v.strip()
    return None


def _get_session_user(token: str) -> str | None:
    if not token:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT username FROM sessions WHERE session_token = ?", (token,)
        ).fetchone()
    return row["username"] if row else None


def _create_session(username: str) -> str:
    token = uuid.uuid4().hex
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (session_token, username) VALUES (?, ?)",
            (token, username),
        )
    return token


def _delete_session(token: str):
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE session_token = ?", (token,))


def _json_response(data: dict, status: int = 200, token: str = "") -> JsonResponse:
    resp = JsonResponse(data, status=status)
    if token:
        resp.set_cookie(
            "session_token", token,
            max_age=604800,   # 7 дней
            httponly=True,
            path="/",
        )
    return resp


def _json_body(request) -> dict:
    try:
        return json.loads(request.body)
    except Exception:
        return {}


# ── Views ─────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class SignupView(View):
    """
    POST /signup.py
    body: {"mode": "signup"|"login", "name":..., "username":..., "age":..., "password":...}
    """

    def post(self, request):
        data     = _json_body(request)
        mode     = data.get("mode", "signup")
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return _json_response({"ok": False, "error": "Заполни все поля."})

        try:
            with get_db() as conn:

                if mode == "login":
                    row = conn.execute(
                        "SELECT * FROM users WHERE username = ?", (username,)
                    ).fetchone()
                    if not row:
                        return _json_response({"ok": False, "error": "Пользователь не найден."})
                    if row["password"] != password:
                        return _json_response({"ok": False, "error": "Неверный пароль."})

                    token = _create_session(username)
                    return _json_response(
                        {"ok": True, "user": {
                            "name": row["name"], "username": row["username"], "age": row["age"]
                        }},
                        token=token,
                    )

                else:  # signup
                    existing = conn.execute(
                        "SELECT id FROM users WHERE username = ?", (username,)
                    ).fetchone()
                    if existing:
                        return _json_response({"ok": False, "error": "Никнейм занят."})

                    name = data.get("name", "").strip()
                    age  = data.get("age", "").strip()
                    conn.execute(
                        "INSERT INTO users (name, username, age, password) VALUES (?,?,?,?)",
                        (name, username, age, password),
                    )
                    token = _create_session(username)
                    return _json_response(
                        {"ok": True, "user": {"name": name, "username": username, "age": age}},
                        token=token,
                    )

        except Exception as e:
            return _json_response({"ok": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class HobbiesView(View):
    """
    GET  /hobbies.py  → список хобби
    POST /hobbies.py  → сохранить выбранные хобби пользователя
    """

    _DEFAULT = [
        "Photography", "Cooking", "Gaming", "Reading", "Hiking",
        "Music", "Travel", "Painting", "Cycling", "Dancing",
        "Swimming", "Yoga", "Coding", "Gardening", "Chess",
        "Writing", "Fishing", "Surfing", "Climbing", "Pottery",
    ]

    def get(self, request):
        return _json_response({"hobbies": self._DEFAULT})

    def post(self, request):
        token    = _extract_token(_cookie_str(request))
        username = _get_session_user(token)
        if not username:
            return _json_response({"ok": False, "error": "Не авторизован."}, status=401)

        data    = _json_body(request)
        hobbies = data.get("hobbies", [])
        if not isinstance(hobbies, list):
            return _json_response({"ok": False, "error": "hobbies must be a list."})

        try:
            with get_db() as conn:
                conn.execute("DELETE FROM hobbies WHERE user_name = ?", (username,))
                conn.executemany(
                    "INSERT INTO hobbies (user_name, hobby) VALUES (?, ?)",
                    [(username, h) for h in hobbies],
                )
            return _json_response({"ok": True})
        except Exception as e:
            return _json_response({"ok": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class QuestionsView(View):
    """
    GET  /questions.py → список вопросов
    POST /questions.py → сохранить ответы
    """

    _DEFAULT_QUESTIONS = [
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

    def get(self, request):
        return _json_response({"questions": self._DEFAULT_QUESTIONS})

    def post(self, request):
        token    = _extract_token(_cookie_str(request))
        username = _get_session_user(token)

        data = _json_body(request)
        if not username:
            username = data.get("username", "").strip()
        if not username:
            return _json_response({"ok": False, "error": "Не авторизован."}, status=401)

        answers = data.get("answers", {})
        hobbies = data.get("hobbies", [])

        try:
            with get_db() as conn:
                conn.execute(
                    "UPDATE users SET answers = ? WHERE username = ?",
                    (json.dumps(answers, ensure_ascii=False), username),
                )
                if hobbies:
                    conn.execute("DELETE FROM hobbies WHERE user_name = ?", (username,))
                    conn.executemany(
                        "INSERT INTO hobbies (user_name, hobby) VALUES (?, ?)",
                        [(username, h) for h in hobbies],
                    )
            return _json_response({"ok": True, "redirect": "dashboard"})
        except Exception as e:
            return _json_response({"ok": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardView(View):
    """
    GET  /dashboard.py → профиль текущего пользователя
    POST /dashboard.py {"action": "logout"} → выход
    """

    def get(self, request):
        token    = _extract_token(_cookie_str(request))
        username = _get_session_user(token)
        if not username:
            return _json_response(
                {"ok": False, "error": "Сессия истекла.", "redirect": "signup"},
                status=401,
            )

        try:
            with get_db() as conn:
                user = conn.execute(
                    "SELECT * FROM users WHERE username = ?", (username,)
                ).fetchone()
                if not user:
                    return _json_response({"ok": False, "error": "Пользователь не найден."})

                hobbies = [
                    r["hobby"] for r in conn.execute(
                        "SELECT hobby FROM hobbies WHERE user_name = ?", (username,)
                    ).fetchall()
                ]

            try:
                answers = json.loads(user["answers"] or "{}")
            except Exception:
                answers = {}

            return _json_response({"ok": True, "user": {
                "name":     user["name"],
                "username": user["username"],
                "age":      user["age"],
                "hobbies":  hobbies,
                "answers":  answers,
            }})

        except Exception as e:
            return _json_response({"ok": False, "error": str(e)}, status=500)

    def post(self, request):
        token = _extract_token(_cookie_str(request))
        data  = _json_body(request)

        if data.get("action") == "logout":
            if token:
                _delete_session(token)
            resp = _json_response({"ok": True, "redirect": "signup"})
            resp.delete_cookie("session_token")
            return resp

        return _json_response({"ok": False, "error": "Неизвестное действие."})