"""
ui_bridge/views.py

Делегирует запросы к существующим обработчикам из ui/:
  signup.handle_request, hobbies.handle_request,
  questions.handle_request, dashboard.handle_request

Каждый handle_request(method, body_bytes, cookie_str) -> dict | (dict, token)
"""

import sys
import json
from pathlib import Path

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# ── Добавляем ui/ в sys.path чтобы импортировать модули напрямую ──────────────
UI_DIR = Path(__file__).resolve().parent.parent.parent / "ui"
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

import signup as _signup
import hobbies as _hobbies
import questions as _questions
import dashboard as _dashboard


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _cookie_str(request) -> str:
    """Собирает строку cookie так же, как это делал BaseHTTPRequestHandler."""
    return request.META.get("HTTP_COOKIE", "")


def _json_response(data: dict, status: int = 200, token: str = "") -> JsonResponse:
    resp = JsonResponse(data, status=status)
    if token:
        resp.set_cookie(
            "session_token", token,
            max_age=604800,   # 7 дней
            httponly=True,
            path="/",
        )
    return resp


# ── Views ─────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class SignupView(View):
    def post(self, request):
        result, token = _signup.handle_request("POST", request.body, _cookie_str(request))
        return _json_response(result, token=token)


@method_decorator(csrf_exempt, name="dispatch")
class HobbiesView(View):
    def get(self, request):
        result = _hobbies.handle_request("GET", b"", _cookie_str(request))
        return _json_response(result)

    def post(self, request):
        result = _hobbies.handle_request("POST", request.body, _cookie_str(request))
        return _json_response(result)


@method_decorator(csrf_exempt, name="dispatch")
class QuestionsView(View):
    def get(self, request):
        result = _questions.handle_request("GET", b"", _cookie_str(request))
        return _json_response(result)

    def post(self, request):
        result = _questions.handle_request("POST", request.body, _cookie_str(request))
        return _json_response(result)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardView(View):
    def get(self, request):
        result = _dashboard.handle_request("GET", b"", _cookie_str(request))
        return _json_response(result)

    def post(self, request):
        result = _dashboard.handle_request("POST", request.body, _cookie_str(request))
        return _json_response(result)