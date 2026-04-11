from django.urls import path
from .views import (
    IndexView,
    SessionListView,
    SessionDetailView,
    SendMessageView,
    ConcludeSessionView,
    LoadSessionView,
    UserSettingsView,
)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),

    # Sessions
    path('api/sessions/',                              SessionListView.as_view(),   name='sessions'),
    path('api/sessions/<int:session_id>/',             SessionDetailView.as_view(), name='session-detail'),
    path('api/sessions/<int:session_id>/send/',        SendMessageView.as_view(),   name='send-message'),
    path('api/sessions/<int:session_id>/conclude/',    ConcludeSessionView.as_view(), name='conclude'),
    path('api/sessions/<int:session_id>/load/',        LoadSessionView.as_view(),   name='load-session'),

    # Settings (custom prompt)
    path('api/settings/', UserSettingsView.as_view(), name='settings'),
]