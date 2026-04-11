"""
hobbies.py — страница выбора хобби.

Читает hobbies.csv через fetch (только чтение — это разрешено браузером).
Выбранные хобби сохраняет в localStorage в черновик пользователя.
"""

import io
import csv
import json
import asyncio
from js import document, window, localStorage, fetch
from pyodide.ffi import create_proxy

# ── утилиты ───────────────────────────────────────────────

def _get_draft() -> dict:
    raw = window.sessionStorage.getItem("draft_user")
    return json.loads(raw) if raw else {}

def _save_draft(draft: dict) -> None:
    window.sessionStorage.setItem("draft_user", json.dumps(draft))

# ── состояние ─────────────────────────────────────────────

selected: set[str] = set()

# ── рендер чипов ──────────────────────────────────────────

def render_chips(hobbies: list[str]) -> None:
    container = document.getElementById("chips-container")
    container.innerHTML = ""
    for hobby in hobbies:
        btn = document.createElement("button")
        btn.className   = "chip"
        btn.textContent = hobby

        def make_handler(h, el):
            def handler(event):
                if h in selected:
                    selected.discard(h)
                    el.classList.remove("selected")
                else:
                    selected.add(h)
                    el.classList.add("selected")
            return create_proxy(handler)

        btn.addEventListener("click", make_handler(hobby, btn))
        container.appendChild(btn)

# ── загрузка CSV ───────────────────────────────────────────

async def load_hobbies() -> None:
    hobbies = []
    try:
        resp     = await fetch("hobbies.csv")
        buf      = await resp.arrayBuffer()
        text     = window.TextDecoder.new("utf-8").decode(buf)
        reader   = csv.DictReader(io.StringIO(text))
        header   = reader.fieldnames or []
        col      = "hobby" if "hobby" in [h.lower() for h in header] else header[0]
        hobbies  = [row[col].strip() for row in reader if row[col].strip()]
    except Exception:
        hobbies = [
            "Photography", "Cooking", "Gaming", "Reading", "Hiking",
            "Music", "Travel", "Painting", "Cycling", "Dancing",
            "Swimming", "Yoga", "Coding", "Gardening", "Chess",
            "Writing", "Fishing", "Surfing", "Climbing", "Pottery",
            "Skateboarding т", "Film", "3D Art", "Drawing",
        ]
    render_chips(hobbies)

asyncio.ensure_future(load_hobbies())

# ── навигация ─────────────────────────────────────────────

def on_back(event=None):
    window.location.href = "signup.html"

def on_continue(event=None):
    draft = _get_draft()
    draft["hobbies"] = list(selected)
    _save_draft(draft)
    window.location.href = "questions.html"

document.getElementById("btn-back").addEventListener("click",     create_proxy(on_back))
document.getElementById("btn-continue").addEventListener("click", create_proxy(on_continue))