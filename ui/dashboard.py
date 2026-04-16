import json
import asyncio
from js import window, document, sessionStorage, fetch, Object
from pyodide.ffi import to_js


async def load_profile():
    user = None
    raw = sessionStorage.getItem("draft_user")
    if raw:
        try:
            user = json.loads(raw)
        except Exception:
            pass

    if not user:
        try:
            opts = to_js({"method": "GET", "credentials": "include"}, dict_converter=Object.fromEntries)
            resp = await fetch("/dashboard.py", opts)
            data = (await resp.json()).to_py()
            if data.get("ok"):
                user = data["user"]
            else:
                window.location.href = "/signup.html"
                return
        except Exception:
            window.location.href = "/signup.html"
            return

    render(user)


def render(u):
    name     = u.get("name") or u.get("username") or "?"
    username = u.get("username", "")
    age      = u.get("age", "")
    hobbies  = u.get("hobbies", [])
    answers  = u.get("answers", {})

    initials = "".join(w[0] for w in name.split() if w).upper()[:2] or "?"
    document.getElementById("avatar").textContent = initials
    document.getElementById("p-name").textContent = name
    meta = f"@{username}" + (f"  ·  age {age}" if age else "")
    document.getElementById("p-meta").textContent = meta

    hobbies_el = document.getElementById("p-hobbies")
    hobbies_el.innerHTML = ""
    if hobbies:
        for h in hobbies:
            tag = document.createElement("span")
            tag.className = "hobby-tag"
            tag.textContent = h
            hobbies_el.appendChild(tag)
    else:
        hobbies_el.innerHTML = '<span style="font-size:11px;color:var(--dimmed)">No hobbies selected</span>'

    answers_el = document.getElementById("p-answers")
    answers_el.innerHTML = ""
    if answers:
        for i, v in answers.items():
            row = document.createElement("div")
            row.className = "profile-answer-row"
            row.innerHTML = (
                f'<span class="answer-label">Q{int(i) + 1}</span>'
                f'<span class="answer-value">{v}</span>'
            )
            answers_el.appendChild(row)


async def logout(event=None):
    sessionStorage.clear()
    try:
        opts = to_js({
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "credentials": "include",
            "body": json.dumps({"action": "logout"}),
        }, dict_converter=Object.fromEntries)
        await fetch("/dashboard.py", opts)
    except Exception:
        pass
    window.location.href = "/signup.html"


document.getElementById("logout-btn").addEventListener(
    "click", lambda e: asyncio.ensure_future(logout())
)

asyncio.ensure_future(load_profile())