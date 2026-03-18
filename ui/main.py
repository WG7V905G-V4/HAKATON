import io
import csv
import js
from pyscript import document
from pyodide.ffi import create_proxy, to_js
import asyncio


# ── Карта ────────────────────────────────────────────────
map_options = js.Object.new()
map_options.zoomControl = False
map_options.attributionControl = False

leaflet_map = js.L.map("map", map_options)
leaflet_map.setView(to_js([32.0, 34.9]), 11)

js.L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    to_js({"maxZoom": 19})
).addTo(leaflet_map)

# ── Иконки ───────────────────────────────────────────────
def create_dot(color):
    opt = js.Object.new()
    opt.className = ""
    opt.html = f'''
    <div style="width:14px;height:14px;background:{color};
    border-radius:50%;border:3px solid #fff;
    box-shadow:0 2px 8px {color};"></div>
    '''
    opt.iconSize = to_js([14, 14])
    opt.iconAnchor = to_js([7, 7])
    return js.L.divIcon(opt)

event_icon = create_dot("#4a8cff")
my_icon    = create_dot("#ff4a4a")

current_marker = [None]
current_line   = [None]
my_location    = [None]

MY_LAT, MY_LNG = MY_LOCATION

# ── Показ на карте ───────────────────────────────────────
def show_on_map(lat, lng, label):
    leaflet_map.invalidateSize()

    if current_marker[0]:
        current_marker[0].remove()
    if current_line[0]:
        current_line[0].remove()

    marker = js.L.marker(to_js([lat, lng]), to_js({"icon": event_icon}))
    marker.addTo(leaflet_map)
    marker.bindPopup(f"<b>{label}</b>")
    marker.openPopup()

    # линия от меня
    if my_location[0]:
        my_lat, my_lng = my_location[0]
        line = js.L.polyline(
            to_js([[my_lat, my_lng], [lat, lng]]),
            to_js({"color": "#ff4a4a", "dashArray": "6,10"})
        )
        line.addTo(leaflet_map)
        current_line[0] = line

    leaflet_map.flyTo(to_js([lat, lng]), 13)
    current_marker[0] = marker

# ── Геолокация ───────────────────────────────────────────
def draw_my_marker(lat, lng):
    marker = js.L.marker(to_js([lat, lng]), to_js({"icon": my_icon}))
    marker.addTo(leaflet_map)
    marker.bindPopup("Я здесь")
    marker.openPopup()

def on_location(pos):
    lat = pos.coords.latitude
    lng = pos.coords.longitude
    print("GPS OK:", lat, lng)

    my_location[0] = (lat, lng)
    draw_my_marker(lat, lng)
    leaflet_map.setView(to_js([lat, lng]), 13)

def on_error(err):
    print("GPS ERROR → fallback")

    lat, lng = MY_LAT, MY_LNG
    my_location[0] = (lat, lng)

    draw_my_marker(lat, lng)
    leaflet_map.setView(to_js([lat, lng]), 13)

js.navigator.geolocation.getCurrentPosition(
    create_proxy(on_location),
    create_proxy(on_error)
)

# ── Карточки ─────────────────────────────────────────────
def build_card_html(row):
    return f"""
    <li class="event-card"
        data-lat="{row['lat']}"
        data-lng="{row['lng']}"
        data-title="{row['title']}">
        <b>{row['title']}</b><br>
        {row['place']}<br>
        {row['time_start']} - {row['time_end']}
    </li>
    """

def make_card_handler(card):
    def handler(event):
        lat = float(card.getAttribute("data-lat"))
        lng = float(card.getAttribute("data-lng"))
        title = card.getAttribute("data-title")
        show_on_map(lat, lng, title)
    return create_proxy(handler)

# ── CSV ──────────────────────────────────────────────────
all_rows = []

async def load_events():
    res = await js.fetch("events.csv")
    text = await res.text()

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    all_rows.extend(rows)

    render_cards(rows)

asyncio.ensure_future(load_events())

# ── Рендер ───────────────────────────────────────────────
def render_cards(rows):
    el = document.getElementById("event-list")
    el.innerHTML = ""

    for r in rows:
        el.insertAdjacentHTML("beforeend", build_card_html(r))

    cards = document.querySelectorAll(".event-card")
    for i in range(cards.length):
        cards[i].addEventListener("click", make_card_handler(cards[i]))