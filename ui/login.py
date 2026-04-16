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


async def handle_login(event=None):
    hide_flash()

    username = document.getElementById("inp-username").value.strip()
    password = document.getElementById("inp-password").value

    if not username or not password:
        show_flash("Please fill in all fields.")
        return

    try:
        payload = json.dumps({
            "mode": "login",
            "username": username,
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
            window.location.href = "/dashboard.html"
        else:
            show_flash(res.get("error", "Invalid username or password."))

    except Exception as e:
        show_flash(f"Error: {e}")


def on_key(event):
    if event.key == "Enter":
        asyncio.ensure_future(handle_login())


document.getElementById("login-btn").addEventListener(
    "click", lambda e: asyncio.ensure_future(handle_login())
)
document.addEventListener("keydown", on_key)