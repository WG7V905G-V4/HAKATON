import json
import asyncio
from js import window, document, sessionStorage, fetch, Object
from pyodide.ffi import to_js


def show_flash(msg, ok=False):
    f = document.getElementById("flash")
    f.textContent = msg
    f.className = "flash " + ("success" if ok else "error")
    f.style.display = "block"


def hide_flash():
    f = document.getElementById("flash")
    f.style.display = "none"


async def handle_signup(event=None):
    hide_flash()

    name     = document.getElementById("inp-name").value.strip()
    username = document.getElementById("inp-username").value.strip()
    age      = document.getElementById("inp-age").value.strip()
    password = document.getElementById("inp-password").value

    if not name or not username or not age or not password:
        show_flash("Please fill in all fields.")
        return

    try:
        payload = json.dumps({
            "mode": "signup",
            "name": name,
            "username": username,
            "age": age,
            "password": password,
        })

        opts = to_js({
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "credentials": "include",
            "body": payload,
        }, dict_converter=Object.fromEntries)

        response = await fetch("/signup.py", opts)
        res = (await response.json()).to_py()

        if res.get("ok"):
            sessionStorage.setItem("draft_user", json.dumps(res.get("user", {})))
            window.location.href = "/hobbies.html"
        else:
            show_flash(res.get("error", "Something went wrong."))

    except Exception as e:
        show_flash(f"Error: {e}")


def on_key(event):
    if event.key == "Enter":
        asyncio.ensure_future(handle_signup())


document.getElementById("signup-btn").addEventListener(
    "click", lambda e: asyncio.ensure_future(handle_signup())
)
document.addEventListener("keydown", on_key)