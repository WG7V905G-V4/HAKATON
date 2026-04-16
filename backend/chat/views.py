import json
from django.http             import JsonResponse
from django.views            import View
from django.views.generic    import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts        import get_object_or_404

from .models  import ChatSession, Message, UserSettings
from .chatbot import get_ai_response, get_conclusion, get_session_for_display


def json_body(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


# ── helpers ────────────────────────────────────────────────────────────────

def _custom_prompt():
    return UserSettings.get_solo().custom_prompt


# ── views ──────────────────────────────────────────────────────────────────

class IndexView(TemplateView):
    template_name = 'index.html'


@method_decorator(csrf_exempt, name='dispatch')
class SessionListView(View):

    def get(self, request):
        sessions = ChatSession.objects.all()
        return JsonResponse(
            {'sessions': [s.to_dict() for s in sessions]},
            status=200,
        )

    def post(self, request):
        session = ChatSession.objects.create()
        greeting = (
            "Welcome. I'm your AI psychological support assistant — "
            "think of me as a compassionate, non-judgmental space where you can speak freely.\n\n"

            "Here is what I can do for you:\n"
            "• Listen deeply and reflect back what you're experiencing\n"
            "• Help you work through difficult emotions, stress, anxiety, or low mood\n"
            "• Apply evidence-based techniques from CBT, mindfulness, and strength-based therapy\n"
            "• Offer psychoeducation — plain-language explanations of what you might be feeling and why\n"
            "• Track patterns across sessions — I remember the themes and progress from our previous talks\n"
            "• Generate a professional session summary at the end of our conversation\n\n"

            "A few things to know before we start:\n"
            "1. I respond in whatever language you write in — Russian, English, Hebrew, Ukrainian, or any other.\n"
            "2. I am not a doctor and will never give a clinical diagnosis. "
            "If you are in crisis, I will always provide emergency resources immediately.\n"
            "3. Everything stays here — your sessions are stored only on your own device.\n"
            "4. When you are ready to close a session, press 'End session' and I will write a structured summary for you.\n\n"

            "How to get the most out of our sessions:\n"
            "• Be as open as you feel comfortable — the more context you share, the more I can help\n"
            "• You can ask me to focus on a specific technique: 'help me reframe this thought', "
            "'guide me through a breathing exercise', 'what does anxiety actually do to the body?'\n"
            "• You can review any past session from the sidebar on the left\n\n"

            "I'm here, fully present. Whenever you're ready — just start talking."
        )
        Message.objects.create(
            session=session,
            role=Message.ROLE_ASSISTANT,
            content=greeting,
        )
        return JsonResponse({'session': session.to_dict()}, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class SessionDetailView(View):

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, pk=session_id)
        return JsonResponse({
            'session':  session.to_dict(),
            'messages': [m.to_dict() for m in session.messages.all()],
        })

    def delete(self, request, session_id):
        session = get_object_or_404(ChatSession, pk=session_id)
        session.delete()
        return JsonResponse({'ok': True})


@method_decorator(csrf_exempt, name='dispatch')
class SendMessageView(View):

    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, pk=session_id)

        if session.concluded:
            return JsonResponse(
                {'error': 'Эта сессия завершена. Начни новый чат.'},
                status=400,
            )

        data    = json_body(request)
        content = data.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Пустое сообщение.'}, status=400)

        user_msg = Message.objects.create(
            session=session,
            role=Message.ROLE_USER,
            content=content,
        )

        bot_text = get_ai_response(
            session.messages.all(),
            current_session_id=session.pk,
            custom_prompt=_custom_prompt(),
        )
        bot_msg = Message.objects.create(
            session=session,
            role=Message.ROLE_ASSISTANT,
            content=bot_text,
        )

        return JsonResponse({
            'user_message': user_msg.to_dict(),
            'bot_message':  bot_msg.to_dict(),
        }, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class ConcludeSessionView(View):

    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, pk=session_id)

        if session.concluded:
            return JsonResponse({'conclusion': session.conclusion})

        conclusion_text = get_conclusion(
            session.messages.all(),
            current_session_id=session.pk,
            custom_prompt=_custom_prompt(),
        )
        Message.objects.create(
            session=session,
            role=Message.ROLE_ASSISTANT,
            content=conclusion_text,
        )
        session.concluded  = True
        session.conclusion = conclusion_text
        session.save()

        return JsonResponse({
            'conclusion': conclusion_text,
            'session':    session.to_dict(),
        })


@method_decorator(csrf_exempt, name='dispatch')
class LoadSessionView(View):
    """
    POST /api/sessions/<id>/load/
    Loads a past session and returns an AI-formatted summary as a chat message.
    The summary is NOT saved to the DB — it's display-only.
    """

    def post(self, request, session_id):
        # Make sure the session exists
        get_object_or_404(ChatSession, pk=session_id)

        trigger_text = get_session_for_display(session_id)

        # Build a fake message list: current active session messages + the trigger
        # Find the latest non-concluded session to use as context
        active = ChatSession.objects.filter(concluded=False).first()
        base_messages = list(active.messages.all()) if active else []

        # Append the trigger as a virtual user message (not saved)
        class _FakeMsg:
            def __init__(self, role, content):
                self.role    = role
                self.content = content

        response_text = get_ai_response(
            base_messages + [_FakeMsg('user', trigger_text)],
            current_session_id=active.pk if active else None,
            custom_prompt=_custom_prompt(),
        )

        return JsonResponse({'message': response_text}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class UserSettingsView(View):
    """
    GET  /api/settings/   — returns current custom_prompt
    POST /api/settings/   — saves custom_prompt (body: {"custom_prompt": "..."})
    """

    def get(self, request):
        return JsonResponse(UserSettings.get_solo().to_dict())

    def post(self, request):
        data   = json_body(request)
        prompt = data.get('custom_prompt', '').strip()[:1000]

        settings_obj = UserSettings.get_solo()
        settings_obj.custom_prompt = prompt
        settings_obj.save()

        return JsonResponse({'ok': True, 'custom_prompt': prompt})