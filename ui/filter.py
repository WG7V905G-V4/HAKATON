import math
from ui.database.sql import *
from ui.hobbies import _extract_token, get_session_user

# --------------------------------------------------
# ГЛОБАЛЬНОЕ СОСТОЯНИЕ (будет обновляться с сервера)
# --------------------------------------------------

user_lat = None
user_lng = None
user_hobbies = None
current_username = None


# --------------------------------------------------
# COOKIE / USER HELPERS
# --------------------------------------------------

def set_request_context(cookie_header: str):
    """
    Вызывай ЭТУ функцию из server.py перед fetch_and_rank_events()
    """
    global current_username, user_hobbies

    token = _extract_token(cookie_header)
    current_username = get_session_user(token) if token else None

    if current_username:
        user_hobbies = load_user_hobbies(current_username)  # ← из БД


# --------------------------------------------------
# DISTANCE
# --------------------------------------------------

def get_distance(lat1, lng1, lat2, lng2):
    R = 6371

    lat1 = math.radians(lat1)
    lng1 = math.radians(lng1)
    lat2 = math.radians(lat2)
    lng2 = math.radians(lng2)

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# --------------------------------------------------
# TAG SIMILARITY
# --------------------------------------------------

def tag_similarity(event_tags, user_hobbies):
    if not user_hobbies:
        return 0

    event_set = set([t.strip().lower() for t in event_tags.split("|") if t.strip()])
    user_set = set([h.strip().lower() for h in user_hobbies])

    if not event_set:
        return 0

    return len(event_set.intersection(user_set)) / len(event_set)


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

async def fetch_and_rank_events():
    events = fetch_all_from_db()

    ranked = []

    for e in events:
        try:
            elat = float(e["lat"])
            elng = float(e["lng"])
        except:
            continue

        # distance score
        dist_score = 0
        if user_lat is not None and user_lng is not None:
            dist = get_distance(user_lat, user_lng, elat, elng)
            dist_score = 1 / (1 + dist)

        # tag score
        tag_score = tag_similarity(e.get("tags", ""), user_hobbies)

        # final score
        score = (tag_score * 0.7) + (dist_score * 0.3)

        e["_score"] = score
        ranked.append(e)

    ranked.sort(key=lambda x: x["_score"], reverse=True)

    return ranked