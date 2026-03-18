import io, csv, js
from pyscript import document
from pyodide.ffi import create_proxy, to_js
from math import radians, sin, cos, sqrt, atan2
import asyncio


from CONST import *


def get_user_hobbies(username):
    mycursor.execute('''
        SELECT hobby FROM activity_hobbies
        JOIN activity_users ON activity_hobbies.activity_id = activity_users.activity_id
        WHERE activity_users.username = %s
    ''', (username,))
    rows = mycursor.fetchall()
    return [row[0] for row in rows]

def get_friends_personality_ranking(username):
    # берём характеры всех друзей
    mycursor.execute('''
        SELECT users.person_t FROM friends
        JOIN users ON friends.username_friend = users.username
        WHERE friends.username = %s
    ''', (username,))
    rows = mycursor.fetchall()

    # считаем сколько раз встречается каждый характер
    counts = {}
    for row in rows:
        person_t = row[0]
        counts[person_t] = counts.get(person_t, 0) + 1

    # сортируем по популярности — первый самый частый
    ranked = sorted(counts, key=lambda x: counts[x], reverse=True)
    return ranked  # например ["INTJ", "ENFP", "ISTP"]

def distance_km(lat1, lng1, lat2, lng2):
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def sort_by_similarity(rows, my_hobbies, my_lat, my_lng, personality_ranking):
    def score(row):
        # хобби
        event_tags = row["tags"].split("|")
        hobby_score = len(set(my_hobbies) & set(event_tags))

        # расстояние
        km = distance_km(my_lat, my_lng, float(row["lat"]), float(row["lng"]))

        # характер участников мероприятия
        participants = row["participants"].split("|")
        personality_score = 0
        for participant in participants:
            mycursor.execute("SELECT person_t FROM users WHERE username = %s", (participant,))
            result = mycursor.fetchone()
            if result:
                person_t = result[0]
                # чем выше в списке характер — тем больше очков
                if person_t in personality_ranking:
                    rank = personality_ranking.index(person_t)  # 0 = первый = лучший
                    personality_score += (len(personality_ranking) - rank)

        return hobby_score - (km / 100) + personality_score

    return sorted(rows, key=score, reverse=True)

async def load_hobbies():
    response = await js.fetch("hobbies.csv")
    buf      = await response.arrayBuffer()
    text     = js.TextDecoder.new("utf-8").decode(buf)
    reader   = csv.DictReader(io.StringIO(text))
    grid     = document.getElementById("hobbies-grid")

    my_hobbies = get_user_hobbies(my_username)
    personality_ranking = get_friends_personality_ranking(my_username)
    my_lat, my_lng = CONST.get_my_location()

    rows = list(reader)
    rows = sort_by_similarity(rows, my_hobbies, my_lat, my_lng, personality_ranking)

    def make_toggle(chip):
        def handler(e):
            chip.classList.toggle("active")
        return create_proxy(handler)

    for row in rows:
        grid.insertAdjacentHTML(
            "beforeend",
            f'<div class="filter-chip" data-id="{row["id"]}">{row["label"]}</div>'
        )

    chips = document.querySelectorAll("#hobbies-grid .filter-chip")
    for i in range(chips.length):
        chips[i].addEventListener("click", make_toggle(chips[i]))

asyncio.ensure_future(load_hobbies())