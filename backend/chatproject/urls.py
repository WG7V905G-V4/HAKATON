from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from ui_bridge.views import SignupView, HobbiesView, QuestionsView, DashboardView

urlpatterns = [
    # ── Стартовая страница → login.html ──────────────────────────────────────
    path("", TemplateView.as_view(template_name="login.html")),

    # ── UI-страницы ───────────────────────────────────────────────────────────
    path("login.html",     TemplateView.as_view(template_name="login.html")),
    path("signup.html",    TemplateView.as_view(template_name="signup.html")),
    path("hobbies.html",   TemplateView.as_view(template_name="hobbies.html")),
    path("questions.html", TemplateView.as_view(template_name="questions.html")),
    path("dashboard.html", TemplateView.as_view(template_name="dashboard.html")),
    path("main.html",      TemplateView.as_view(template_name="main.html")),

    # ── API-эндпоинты (совместимы с ui/server.py) ─────────────────────────────
    path("signup.py",    SignupView.as_view()),
    path("hobbies.py",   HobbiesView.as_view()),
    path("questions.py", QuestionsView.as_view()),
    path("dashboard.py", DashboardView.as_view()),

    # ── Существующий чат ──────────────────────────────────────────────────────
    path("chat/", include("chat.urls")),

] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])