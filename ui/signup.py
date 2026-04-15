from pyscript import document, window
import pyodide.http
import json

async def check_username(event):
    username_input = document.querySelector("#inp-username")
    username = username_input.value.strip()
    flash_box = document.querySelector("#flash")

    if not username:
        return

    # Отправляем запрос на бэкенд для проверки
    try:
        response = await pyodide.http.pyfetch(
            url=f"/api/check-username/?username={username}",
            method="GET"
        )
        if response.status == 400:
            data = await response.json()
            flash_box.innerText = data.get("error", "Username taken")
            flash_box.style.display = "block"
            flash_box.className = "flash error"
            username_input.style.borderColor = "var(--c-error)"
        else:
            flash_box.style.display = "none"
            username_input.style.borderColor = "var(--c-input-border-focus)"
    except Exception as e:
        print(f"Error checking username: {e}")

async def save_step_one(event):
    # Собираем данные из полей
    data = {
        "name": document.querySelector("#inp-name").value,
        "username": document.querySelector("#inp-username").value,
        "age": document.querySelector("#inp-age").value,
        "password": document.querySelector("#inp-password").value
    }
    
    # Сохраняем в LocalStorage браузера
    window.localStorage.setItem("signup_data", json.dumps(data))
    # Переходим на следующую страницу
    window.location.href = "hobbies.html"

# Привязываем события
document.querySelector("#inp-username").onblur = check_username
document.querySelector("#btn-continue").onclick = save_step_one