"""
questions.py — страница с вопросами.

Читает questions.csv через fetch.
Ответы + черновик профиля сохраняет в localStorage.
После сабмита финализирует запись пользователя:
  localStorage["user:<username>"] = {...полный профиль...}
"""

import io
import csv
import json
import asyncio
from js import document, window, localStorage, fetch
from pyodide.ffi import create_proxy

# ── черновик ──────────────────────────────────────────────

def _get_draft() -> dict:
    raw = window.sessionStorage.getItem("draft_user")
    return json.loads(raw) if raw else {}

def _save_draft(draft: dict) -> None:
    window.sessionStorage.setItem("draft_user", json.dumps(draft))

# ── состояние ─────────────────────────────────────────────

answers: dict[int, str] = {}   # {question_index: selected_option}

# ── рендер ────────────────────────────────────────────────

def render_questions(questions: list[dict]) -> None:
    scroll = document.getElementById("q-scroll")
    scroll.innerHTML = ""

    for i, q in enumerate(questions):
        block = document.createElement("div")
        block.className = "q-block anim"
        block.style.animationDelay = f"{0.07 * i + 0.1}s"

        title = document.createElement("div")
        title.className   = "q-section-title"
        title.textContent = q["question"]
        block.appendChild(title)

        opts_wrap = document.createElement("div")
        opts_wrap.className = "q-options"

        for opt in q["options"]:
            btn = document.createElement("button")
            btn.className   = "option-btn"
            btn.textContent = opt

            def make_handler(idx, value, container, el):
                def handler(event):
                    # снимаем выбор со всех вариантов этого вопроса
                    all_opts = container.querySelectorAll(".option-btn")
                    for j in range(all_opts.length):
                        all_opts[j].classList.remove("selected")
                    el.classList.add("selected")
                    answers[idx] = value
                return create_proxy(handler)

            btn.addEventListener("click", make_handler(i, opt, opts_wrap, btn))
            opts_wrap.appendChild(btn)

        block.appendChild(opts_wrap)
        scroll.appendChild(block)

# ── загрузка CSV ───────────────────────────────────────────
# Формат: question,option1,option2,option3,option4

async def load_questions() -> None:
    questions = []
    try:
        resp   = await fetch("questions.csv")
        buf    = await resp.arrayBuffer()
        text   = window.TextDecoder.new("utf-8").decode(buf)
        reader = csv.DictReader(io.StringIO(text))
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
    except Exception:
        questions = [
            {
                "question": "How do you prefer to spend your evenings?",
                "options":  ["Reading a book", "Watching movies",
                             "Going out with friends", "Playing video games"],
            },
            {
                "question": "What kind of music do you enjoy most?",
                "options":  ["Pop", "Rock / Metal", "Electronic / DJ", "Classical / Jazz"],
            },
            {
                "question": "How active are you on a typical day?",
                "options":  ["Very active – gym or sport daily",
                             "Moderately active – walks",
                             "Mostly sedentary – office work",
                             "It varies a lot"],
            },
            {
                "question": "What's your ideal vacation?",
                "options":  ["Beach & relaxation", "City exploration",
                             "Nature & hiking", "Road trip"],
            },
            {
                "question": "How do you handle stressful situations?",
                "options":  ["I talk to someone", "I take a walk or exercise",
                             "I distract myself", "I prefer to be alone"],
            },
        ]
    render_questions(questions)

asyncio.ensure_future(load_questions())

# ── финализация профиля ────────────────────────────────────

def finalize_user() -> None:
    """Записывает полный профиль в localStorage["user:<username>"]."""
    draft = _get_draft()
    draft["answers"] = {str(k): v for k, v in answers.items()}

    username = draft.get("username", "")
    if not username:
        window.location.href = "signup.html"
        return

    # читаем уже сохранённую запись (с паролем) и обновляем её
    key = f"user:{username.lower()}"
    raw = localStorage.getItem(key)
    if raw:
        stored = json.loads(raw)
        stored["hobbies"] = draft.get("hobbies", [])
        stored["answers"] = draft["answers"]
        localStorage.setItem(key, json.dumps(stored))
    else:
        # на случай если запись почему-то не сохранилась
        localStorage.setItem(key, json.dumps(draft))

    _save_draft(draft)   # обновляем черновик для dashboard

# ── навигация ─────────────────────────────────────────────

def on_back(event=None):
    window.location.href = "hobbies.html"

def on_continue(event=None):
    finalize_user()
    window.location.href = "dashboard.html"

document.getElementById("btn-back").addEventListener("click",     create_proxy(on_back))
document.getElementById("btn-continue").addEventListener("click", create_proxy(on_continue))