import js
import asyncio
import time

_last_request_time = 0

async def geocode(address):
    global _last_request_time

    # лимит 1 запрос / секунда
    now = time.time()
    wait = 1.0 - (now - _last_request_time)
    if wait > 0:
        await asyncio.sleep(wait)

    _last_request_time = time.time()

    url = (
        "https://nominatim.openstreetmap.org/search"
        f"?q={js.encodeURIComponent(address)}"
        "&format=json&limit=1"
    )

    resp = await js.fetch(url)
    data_text = await resp.text()
    data = js.JSON.parse(data_text)

    if not data.length:
        return None

    lat = float(data[0].lat)
    lng = float(data[0].lon)

    return lat, lng

result = await geocode("Tel Aviv")

if result:
    lat, lng = result



import math

def get_distance(lat1, lng1, lat2, lng2):
    R = 6371  # радиус Земли в км

    lat1 = math.radians(lat1)
    lng1 = math.radians(lng1)
    lat2 = math.radians(lat2)
    lng2 = math.radians(lng2)

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


import js

async def get_user_location():
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    def success(pos):
        lat = pos.coords.latitude
        lng = pos.coords.longitude
        future.set_result((lat, lng))

    def error(err):
        future.set_result((None, None))

    js.navigator.geolocation.getCurrentPosition(success, error)

    return await future



