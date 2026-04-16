import json
import asyncio
from js import window, document, sessionStorage, fetch, Object
from pyodide.ffi import to_js

selected = set()


def show_flash(msg):
    f = document.getElementById("flash")
    if f:
        f.textContent = msg
        f.style.display = "block"


async def load_hobbies():
    try:
        opts = to_js({"method": "GET", "credentials": "include"}, dict_converter=Object.fromEntries)
        resp = await fetch("/hobbies.py", opts)
        data = (await resp.json()).to_py()
        hobbies = data.get("hobbies", [])
    except Exception as e:
        show_flash(f"Load error: {e}")
        return
    render(hobbies)


def render(hobbies):
    wrap = document.getElementById("chips-container")
    wrap.innerHTML = ""
    for hobby in hobbies:
        btn = document.createElement("button")
        btn.className = "chip"
        btn.textContent = hobby

        def make_toggle(h, b):
            def toggle(event):
                if h in selected:
                    selected.discard(h)
                    b.classList.remove("selected")
                else:
                    selected.add(h)
                    b.classList.add("selected")
            return toggle

        btn.addEventListener("click", make_toggle(hobby, btn))
        wrap.appendChild(btn)


async def go_continue(event=None):
    hobbies = list(selected)
    try:
        payload = json.dumps({"hobbies": hobbies})
        opts = to_js({
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "credentials": "include",
            "body": payload,
        }, dict_converter=Object.fromEntries)
        await fetch("/hobbies.py", opts)
    except Exception as e:
        show_flash(f"Save error: {e}")
        return

    draft = {}
    raw = sessionStorage.getItem("draft_user")
    if raw:
        try:
            draft = json.loads(raw)
        except Exception:
            draft = {}
    draft["hobbies"] = hobbies
    sessionStorage.setItem("draft_user", json.dumps(draft))
    window.location.href = "/questions.html"


def go_back(event=None):
    window.history.back()


document.getElementById("btn-continue").addEventListener(
    "click", lambda e: asyncio.ensure_future(go_continue())
)
document.getElementById("btn-back").addEventListener("click", go_back)

asyncio.ensure_future(load_hobbies())