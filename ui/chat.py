import js
import asyncio
from pyscript import document
from pyodide.ffi import create_proxy, to_js


def add_message(text, role):
    messages_el = document.getElementById("chat-messages")
    div = document.createElement("div")
    div.className = "chat-msg chat-msg--" + ("user" if role == "user" else "bot")
    div.textContent = text
    messages_el.appendChild(div)
    messages_el.scrollTop = messages_el.scrollHeight


def add_typing():
    messages_el = document.getElementById("chat-messages")
    div = document.createElement("div")
    div.className = "chat-msg chat-msg--bot"
    div.id = "typing-indicator"
    div.textContent = "..."
    messages_el.appendChild(div)
    messages_el.scrollTop = messages_el.scrollHeight


def remove_typing():
    t = document.getElementById("typing-indicator")
    if t:
        t.remove()


def get_csrf():
    for cookie in js.document.cookie.split(";"):
        cookie = cookie.strip()
        if cookie.startswith("csrftoken="):
            return cookie.split("=")[1]
    return ""


async def send_chat(conclude=False):
    input_el = document.getElementById("chat-input")
    text = input_el.value.strip()

    if not text and not conclude:
        return

    if not conclude:
        add_message(text, "user")
        input_el.value = ""

    add_typing()

    try:
        url = "/chat/conclude/" if conclude else "/chat/message/"


        fetch_opts = to_js({
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "X-CSRFToken": get_csrf()
            },
            "body": js.JSON.stringify(to_js({"message": text}))
        }, dict_converter=js.Object.fromEntries)

        resp = await js.fetch(url, fetch_opts)
        data_text = await resp.text()
        
        # временно показываем сырой ответ
        add_message(f"DEBUG: [{resp.status}] {data_text[:200]}", "bot")
        remove_typing()

    except Exception as e:
        remove_typing()
        add_message(f"Ошибка: {str(e)}", "bot")

def on_end_click(event):
    asyncio.ensure_future(send_chat(True))


def on_keydown(event):
    if event.key == "Enter" and not event.shiftKey:
        event.preventDefault()
        asyncio.ensure_future(send_chat(False))


def init_chat():
    document.getElementById("chat-send").addEventListener(
        "click", create_proxy(on_send_click)
    )
    document.getElementById("chat-end").addEventListener(
        "click", create_proxy(on_end_click)
    )
    document.getElementById("chat-input").addEventListener(
        "keydown", create_proxy(on_keydown)
    )


document.getElementById("chat-send").addEventListener(
    "click", create_proxy(on_send_click)
)
document.getElementById("chat-end").addEventListener(
    "click", create_proxy(on_end_click)
)
document.getElementById("chat-input").addEventListener(
    "keydown", create_proxy(on_keydown)
)