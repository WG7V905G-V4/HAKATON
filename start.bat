@echo off
echo Starting Django...
start cmd /k "cd /d %~dp0 && .venv\Scripts\activate && cd backend && python manage.py runserver --noreload"
timeout /t 2 >nul
start http://127.0.0.1:8000