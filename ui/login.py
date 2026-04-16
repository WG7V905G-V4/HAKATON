from pyweb import pydom
from js import sessionStorage, window
from pyodide.http import pyfetch
import json

async def handle_login(event=None):
    # Get form values
    username = pydom["#inp-username"][0].value.strip()
    password = pydom["#inp-password"][0].value
    
    # Clear previous flash message
    flash = pydom["#flash"][0]
    flash.style.display = "none"
    
    # Validation
    if not username or not password:
        flash.textContent = "Please fill in all fields."
        flash.className = "flash error"
        flash.style.display = "block"
        return
    
    try:
        # Send request to server
        response = await pyfetch("/signup.py", method="POST",
                                headers={"Content-Type": "application/json"},
                                body=json.dumps({"mode": "login", "username": username,
                                               "password": password}))
        res = await response.json()
        
        if res.get("ok"):
            sessionStorage.setItem("draft_user", json.dumps(res.get("user")))
            window.location.href = "dashboard.html"
        else:
            flash.textContent = res.get("error", "Invalid username or password.")
            flash.className = "flash error"
            flash.style.display = "block"
    except Exception as e:
        # Fallback for server error
        sessionStorage.setItem("draft_user", json.dumps({"username": username}))
        window.location.href = "dashboard.html"

def on_enter(event):
    if event.key == "Enter":
        handle_login()

# Setup event listeners
pydom["#login-btn"][0].onclick = handle_login
pydom.window.document.addEventListener("keydown", on_enter)