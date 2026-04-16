import json
import asyncio
from js import window, document, sessionStorage, fetch, Object
from pyodide.ffi import to_js

questions_data = []
answers = {}


def show_flash(msg):
    f = document.getElementById("flash")
    if f:
        f.textContent = msg
        f.style.display = "block"


async def load_questions():
    global questions_data
    try:
        opts = to_js({"method": "GET", "credentials": "include"}, dict_converter=Object.fromEntries)
        resp = await fetch("/questions.py", opts)
        data = (await resp.json()).to_py()
        questions_data = data.get("questions", [])
    except Exception as e:
        show_flash(f"Load error: {e}")
        return
    render(questions_data)


def render(questions):
    scroll = document.getElementById("q-scroll")
    scroll.innerHTML = ""
    for i, q in enumerate(questions):
        block = document.createElement("div")
        block.className = "q-block anim"
        block.style.animationDelay = f"{0.07 * i + 0.1}s"

        title = document.createElement("div")
        title.className = "q-section-title"
        title.textContent = q["question"]
        block.appendChild(title)

        opts_div = document.createElement("div")
        opts_div.className = "q-options"

        for opt in q["options"]:
            btn = document.createElement("button")
            btn.className = "option-btn"
            btn.textContent = opt

            def make_select(idx, option, container, button):
                def select(event):
                    for b in container.querySelectorAll(".option-btn"):
                        b.classList.remove("selected")
                    button.classList.add("selected")
                    answers[idx] = option
                return select

            btn.addEventListener("click", make_select(i, opt, opts_div, btn))
            opts_div.appendChild(btn)

        block.appendChild(opts_div)
        scroll.appendChild(block)


async def go_continue(event=None):
    for i in range(len(questions_data)):
        if i not in answers:
            show_flash(f"Please answer question #{i + 1}")
            return

    draft = {}
    raw = sessionStorage.getItem("draft_user")
    if raw:
        try:
            draft = json.loads(raw)
        except Exception:
            draft = {}
    draft["answers"] = {str(k): v for k, v in answers.items()}
    sessionStorage.setItem("draft_user", json.dumps(draft))

    try:
        payload = json.dumps(draft)
        opts = to_js({
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "credentials": "include",
            "body": payload,
        }, dict_converter=Object.fromEntries)
        resp = await fetch("/questions.py", opts)
        data = (await resp.json()).to_py()
        if data.get("ok"):
            window.location.href = "/dashboard.html"
        else:
            show_flash(data.get("error", "Error saving answers."))
    except Exception:
        window.location.href = "/dashboard.html"


def go_back(event=None):
    window.history.back()


document.getElementById("btn-continue").addEventListener(
    "click", lambda e: asyncio.ensure_future(go_continue())
)
document.getElementById("btn-back").addEventListener("click", go_back)

asyncio.ensure_future(load_questions())