from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# 1. Этот роут просто открывает твое окно в браузере
@app.route('/')
def index():
    return render_template('index.html')


# 2. Этот роут ловит данные из формы
@app.route('/signup.py', methods=['POST'])
def signup():
    data = request.get_json()

    # ВОТ ОНИ — ТВОИ ПЕРЕМЕННЫЕ!
    user_name = data.get('name')
    user_age = data.get('age')
    username = data.get('username')

    # Проверка в консоли Python
    print("\n" + "=" * 30)
    print(f"ПОЛУЧЕНЫ ДАННЫЕ С САЙТА:")
    print(f"Имя: {user_name}")
    print(f"Возраст: {user_age}")
    print(f"Никнейм: {username}")
    print("=" * 30 + "\n")

    # Отправляем ответ обратно в браузер
    return jsonify({"ok": True, "redirect": "dashboard"})


if __name__ == '__main__':
    app.run(debug=True)