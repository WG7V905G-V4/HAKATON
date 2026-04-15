import math

# --- расстояние (как ты дал) ---
def get_distance(lat1, lng1, lat2, lng2):
    R = 6371  # km

    lat1 = math.radians(lat1)
    lng1 = math.radians(lng1)
    lat2 = math.radians(lat2)
    lng2 = math.radians(lng2)

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# --- пользователь (пока None как ты просил) ---
user_lat = None
user_lng = None
user_hobbies = None  # список хобби, пока None


def tag_similarity(event_tags, user_hobbies):
    if not user_hobbies:
        return 0

    event_set = set([t.strip().lower() for t in event_tags.split("|") if t.strip()])
    user_set = set([h.strip().lower() for h in user_hobbies])

    if not event_set:
        return 0

    return len(event_set.intersection(user_set)) / len(event_set)


def fetch_and_rank_events():
    """
    Берёт события из БД (fetch_all_from_db),
    фильтрует и сортирует по:
    1) схожести тегов
    2) расстоянию до пользователя
    """

    events = fetch_all_from_db()  # <- не трогаем SQL, просто получаем копию

    ranked = []

    for e in events:
        try:
            elat = float(e["lat"])
            elng = float(e["lng"])
        except:
            continue

        # --- distance ---
        dist_score = 0
        if user_lat is not None and user_lng is not None:
            dist = get_distance(user_lat, user_lng, elat, elng)
            dist_score = 1 / (1 + dist)  # чем ближе, тем больше score

        # --- tag similarity ---
        tag_score = tag_similarity(e.get("tags", ""), user_hobbies)

        # --- итоговый score ---
        score = (tag_score * 0.7) + (dist_score * 0.3)

        e["_score"] = score
        ranked.append(e)

    # сортировка ТОЛЬКО в памяти (DB не меняется)
    ranked.sort(key=lambda x: x["_score"], reverse=True)

    return ranked