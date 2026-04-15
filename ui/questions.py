from pyscript import document, window
import pyodide.http
import json

async def finish_registration(event):
    # Достаем ранее сохраненные данные
    base_data = json.loads(window.localStorage.getItem("signup_data") or "{}")
    hobbies = json.loads(window.localStorage.getItem("selected_hobbies") or "[]")
    
    # Собираем ответы на вопросы (логика зависит от вашей разметки в q-scroll)
    answers = {}
    # Пример: собираем все выбранные кнопки в блоках вопросов
    # ... (логика сбора селекторов) ...

    full_profile = {
        **base_data,
        "hobbies": hobbies,
        "answers": answers
    }

    try:
        response = await pyodide.http.pyfetch(
            url="/api/register/",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(full_profile)
        )
        
        if response.ok:
            window.localStorage.clear() # Чистим кэш
            window.location.href = "main.html" # Редирект
        else:
            error_data = await response.json()
            window.alert(f"Registration failed: {error_data.get('error')}")
            
    except Exception as e:
        window.alert(f"Server error: {e}")

document.querySelector("#btn-continue").onclick = finish_registration