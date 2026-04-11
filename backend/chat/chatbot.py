import os
from django.conf import settings
from huggingface_hub import InferenceClient

# ── System prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a compassionate and highly professional AI psychiatrist and psychotherapist assistant.

YOUR CORE APPROACH:
- Listen deeply and attentively — the user's feelings come first
- Never judge, dismiss, or minimise what the user shares
- Respond in the EXACT SAME LANGUAGE the user writes in (Russian, English, Ukrainian, etc.)
- Ask one thoughtful follow-up question at a time — do not overwhelm
- Validate emotions before offering any advice or techniques
- Keep replies conversational and warm, not clinical or listy
- Typical response length: 3-6 sentences

THERAPEUTIC TECHNIQUES YOU USE:
- Active listening and reflective responses
- CBT (cognitive-behavioural therapy) — gently challenge distorted thinking
- Mindfulness cues when appropriate
- Psychoeducation — brief, plain-language explanations of psychological concepts
- Strength-based focus — point out the user's resilience and resources

STRICT RULES:
- Never provide a clinical diagnosis — you are a supportive AI, not a doctor
- For crisis situations (suicidal thoughts, self-harm, abuse) always respond with empathy AND recommend contacting a crisis line or professional immediately
- Do NOT give long bullet-point lists unless explicitly asked
- Do NOT start every reply with "I understand" — vary your opening phrases
- Do NOT use emoji in any response

CRISIS RESOURCES (include when relevant):
- Russia: 8-800-2000-122 (free)
- International: https://findahelpline.com

CONCLUSION MODE (activated when the system requests a session summary):
When asked for a conclusion, write a structured psychological session summary in the SAME LANGUAGE as the conversation.

FORMAT RULES FOR SUMMARY — follow exactly:
- No emoji anywhere
- No decorative lines or borders (no ===, ---, ***  etc.)
- Use a plain numbered list with bold section titles
- Separate each section with a blank line
- The title must be plain text: "Итог сессии" (or translated equivalent)

EXAMPLE FORMAT:
Итог сессии

1. Основные темы
[text here]

2. Эмоциональное состояние
[text here]

3. Сильные стороны
[text here]

4. Рекомендации
[text here]

5. Заключение
[text here]

Make the summary warm, professional, and genuinely helpful."""

CONCLUSION_TRIGGER = (
    "\n\n[SYSTEM: The user has ended the session. "
    "Please write a full session summary now. "
    "IMPORTANT: Do NOT use any emoji, decorative borders or lines. "
    "Use plain numbered sections separated by blank lines. "
    "Start with just the plain title 'Итог сессии' (or the language equivalent), then a blank line, then sections 1-5.]"
)

SESSION_HISTORY_PREFIX = """[SYSTEM: Below are summaries of the user's previous sessions for context. 
Use them to provide continuity and reference past themes when relevant. 
Do NOT mention these summaries unless the user asks.]

PREVIOUS SESSIONS:
{summaries}

[END OF PREVIOUS SESSIONS]

"""

LOAD_SESSION_TRIGGER = """[SYSTEM: The user wants to review a past session. 
Please present the following session record in a clear, warm, readable format in the conversation language.
Do not add analysis — just present it naturally.]

Session from {date_label}:
{messages}
"""


def _get_recent_session_summaries(current_session_id=None, limit=5):
    """
    Fetch the last `limit` concluded sessions (excluding current) 
    and return their conclusions as a formatted string.
    """
    try:
        from chat.models import ChatSession
        qs = ChatSession.objects.filter(concluded=True)
        if current_session_id:
            qs = qs.exclude(id=current_session_id)
        sessions = qs.order_by('-created_at')[:limit]

        if not sessions:
            return None

        parts = []
        for i, s in enumerate(reversed(list(sessions)), 1):
            parts.append(
                f"--- Session {i} ({s.date_label}) ---\n{s.conclusion or '(no summary)'}"
            )
        return "\n\n".join(parts)
    except Exception:
        return None


def _build_messages(db_messages, add_conclusion_trigger=False,
                    current_session_id=None, custom_prompt=None):
    # Build the full system prompt
    system_content = SYSTEM_PROMPT

    # Inject custom user prompt if provided
    if custom_prompt and custom_prompt.strip():
        system_content += (
            f"\n\nADDITIONAL INSTRUCTIONS FROM THE USER (follow these alongside the rules above):\n"
            f"{custom_prompt.strip()}"
        )

    # Inject recent session summaries for context
    summaries = _get_recent_session_summaries(current_session_id=current_session_id)
    if summaries:
        system_content = SESSION_HISTORY_PREFIX.format(summaries=summaries) + system_content

    messages = [{"role": "system", "content": system_content}]

    for m in db_messages:
        role = "assistant" if m.role == "assistant" else "user"
        messages.append({"role": role, "content": m.content})

    if add_conclusion_trigger:
        messages.append({"role": "user", "content": CONCLUSION_TRIGGER})

    return messages


def _clean_conclusion(text: str) -> str:
    """
    Post-process the conclusion to strip any stray decorative characters
    the model might still emit, and normalise blank lines between sections.
    """
    import re

    lines = text.splitlines()
    cleaned = []
    for line in lines:
        # Remove lines that are only decorative (=, -, *, ~, box-drawing chars)
        if re.match(r'^[\s═─=\-\*~]+$', line):
            continue
        # Strip leading/trailing whitespace from each line
        cleaned.append(line.rstrip())

    # Collapse 3+ consecutive blank lines into 2
    result = re.sub(r'\n{3,}', '\n\n', "\n".join(cleaned))
    return result.strip()


def _get_client_and_model():
    api_key = getattr(settings, 'HF_API_KEY', '') or os.getenv('HF_API_KEY', '')
    model = getattr(settings, 'HF_MODEL', '') or os.getenv('HF_MODEL', 'deepseek-ai/DeepSeek-R1')
    return api_key, model


def get_ai_response(db_messages, current_session_id=None, custom_prompt=None) -> str:
    api_key, model = _get_client_and_model()

    if not api_key or api_key.startswith('hf_YOUR'):
        return "HuggingFace API key is not set. Add your key to HF_API_KEY."

    try:
        client = InferenceClient(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=_build_messages(
                db_messages,
                current_session_id=current_session_id,
                custom_prompt=custom_prompt,
            ),
            max_tokens=600,
            temperature=0.75,
        )
        text = completion.choices[0].message.content.strip()
        return text or "I'm here — just give me a moment… Please try writing again."
    except Exception as e:
        return f"Connection/model error: {e}"


def get_conclusion(db_messages, current_session_id=None, custom_prompt=None) -> str:
    api_key, model = _get_client_and_model()

    if not api_key or api_key.startswith('hf_YOUR'):
        return "HuggingFace API key is not set. Add your key to HF_API_KEY."

    try:
        client = InferenceClient(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=_build_messages(
                db_messages,
                add_conclusion_trigger=True,
                current_session_id=current_session_id,
                custom_prompt=custom_prompt,
            ),
            max_tokens=700,
            temperature=0.7,
        )
        text = completion.choices[0].message.content.strip()
        return _clean_conclusion(text) if text else "Could not generate session summary."
    except Exception as e:
        return f"Connection/model error: {e}"


def get_session_for_display(session_id: int) -> str:
    """
    Load a specific session's messages and format them for display in chat.
    Returns a formatted string that the AI will present to the user.
    """
    try:
        from chat.models import ChatSession, Message
        session = ChatSession.objects.get(id=session_id)
        messages = Message.objects.filter(session=session).order_by('timestamp')

        lines = []
        for m in messages:
            role_label = "Вы" if m.role == "user" else "Ассистент"
            lines.append(f"{role_label}: {m.content}")

        formatted = "\n\n".join(lines)
        return LOAD_SESSION_TRIGGER.format(
            date_label=session.date_label,
            messages=formatted,
        )
    except Exception as e:
        return f"[SYSTEM: Could not load session {session_id}: {e}]"