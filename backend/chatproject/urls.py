from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', TemplateView.as_view(template_name='main.html')),
    path('chat/', include('chat.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])