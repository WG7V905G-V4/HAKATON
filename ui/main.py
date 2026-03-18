import io
import csv
import js
from pyscript import document
from pyodide.ffi import create_proxy, to_js
import asyncio
from CONST import *

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

icon_options = js.Object.new()
icon_options.className  = ""
icon_options.html       = (
    '<div style="width:14px;height:14px;background:#4a8cff;'
    'border-radius:50%;border:3px solid #fff;'
    'box-shadow:0 2px 8px rgba(74,140,255,0.6);"></div>'
)
icon_options.iconSize   = to_js([14, 14])
icon_options.iconAnchor = to_js([7, 7])
marker_icon = js.L.divIcon(icon_options)
current_marker = [None]
current_line   = [None]  # линия маршрута
my_location    = [None]  # мои координаты

# ─────────────────────────────────────────────────────────
# 👇 ВВЕДИ СВОИ КООРДИНАТЫ ЗДЕСЬ

MY_LAT, MY_LNG = MY_LOCATION
# ─────────────────────────────────────────────────────────

def show_on_map(lat, lng, label):
    leaflet_map.invalidateSize()
    if current_marker[0] is not None:
        current_marker[0].remove()
    if current_line[0] is not None:
        current_line[0].remove()

    marker_opts = js.Object.new()
    marker_opts.icon = marker_icon
    marker = js.L.marker(to_js([lat, lng]), marker_opts)
    marker.addTo(leaflet_map)
    marker.bindPopup(f'<span style="font-weight:600;font-size:13px">{label}</span>')
    marker.openPopup()

    # рисуем линию от меня до мероприятия
    if my_location[0] is not None:
        my_lat, my_lng = my_location[0]
        line = js.L.polyline(to_js([[my_lat, my_lng], [lat, lng]]), to_js({"color": "#ff4a4a", "weight": 3, "dashArray": "6,10"}))
        line.addTo(leaflet_map)
        current_line[0] = line

    zoom      = 13
    ui_px     = 52 + 390
    offset_px = ui_px / 2
    pt         = leaflet_map.project(to_js([lat, lng]), zoom)
    shifted    = js.L.point(pt.x - offset_px, pt.y)
    new_center = leaflet_map.unproject(shifted, zoom)
    fly_opts          = js.Object.new()
    fly_opts.duration = 1.0
    leaflet_map.flyTo(new_center, zoom, fly_opts)
    current_marker[0] = marker

# ── Панели ───────────────────────────────────────────────
panels  = ["panel-1", "panel-2", "panel-3", "panel-4"]
buttons = ["btn-1",   "btn-2",   "btn-3",   "btn-4"  ]
current_open = [None]

def make_toggle(panel_id, btn_id):
    def handler(event):
        if current_open[0] == panel_id:
            return
        for p in panels:
            document.getElementById(p).classList.remove("open")
        for b in buttons:
            document.getElementById(b).classList.remove("active")
        body = document.querySelector("body")
        body.classList.remove("panel-1-open")
        document.getElementById(panel_id).classList.add("open")
        document.getElementById(btn_id).classList.add("active")
        current_open[0] = panel_id
        if panel_id == "panel-1":
            body.classList.add("panel-1-open")
    return create_proxy(handler)

for p, b in zip(panels, buttons):
    document.getElementById(b).addEventListener("click", make_toggle(p, b))

# ── Построение карточки ───────────────────────────────────
def build_card_html(row):
    participants_html = ""
    raw = row.get("participants", "").strip()
    if raw:
        for name in raw.split("|"):
            name = name.strip()
            if name:
                participants_html += f"""
                <div class="participant">
                  <div class="participant-avatar"></div>
                  <span class="participant-name">{name}</span>
                </div>"""

    return f"""
    <li class="event-card"
        data-lat="{row['lat'].strip()}"
        data-lng="{row['lng'].strip()}"
        data-title="{row['title'].strip()}">
      <div class="event-main">
        <div class="event-header">
          <span class="event-dot"></span>
          <span class="event-author">{row['author'].strip()}</span>
        </div>
        <div class="event-title">{row['title'].strip()}</div>
        <div class="event-meta">
          <span class="event-tags">{', '.join(row['tags'].strip().split('|'))}</span>
          <span class="event-time">{row['time_start'].strip()} – {row['time_end'].strip()}</span>
          <span class="event-place">{row['place'].strip()}</span>
        </div>
      </div>
      <div class="event-expandable">
        <p class="event-desc">{row['desc'].strip()}</p>
        <div class="event-participants">{participants_html}</div>
        <button class="btn-join">join</button>
      </div>
    </li>"""

# ── Хендлер карточки ─────────────────────────────────────
def make_card_handler(card):
    def handler(event):
        if event.target.classList.contains("btn-join"):
            return
        all_cards = document.querySelectorAll(".event-card")
        for i in range(all_cards.length):
            all_cards[i].classList.remove("selected")
        card.classList.add("selected")
        lat   = float(card.getAttribute("data-lat"))
        lng   = float(card.getAttribute("data-lng"))
        label = card.getAttribute("data-title")
        show_on_map(lat, lng, label)
    return create_proxy(handler)

# ── Загрузка CSV ─────────────────────────────────────────
all_rows = []

async def load_events():
    response = await js.fetch("events.csv")
    buf      = await response.arrayBuffer()
    decoder  = js.TextDecoder.new("utf-8")
    text     = decoder.decode(buf)

    reader = csv.DictReader(io.StringIO(text))
    rows   = list(reader)
    all_rows.extend(rows)

    render_cards(rows)

    seen = set()
    filter_bar = document.getElementById("filter-bar")
    for row in rows:
        for tag in row.get("tags", "").split("|"):
            tag = tag.strip()
            if tag and tag not in seen:
                seen.add(tag)
                filter_bar.insertAdjacentHTML(
                    "beforeend",
                    f'<div class="filter-chip" data-tag="{tag}">{tag}</div>'
                )

    chips = document.querySelectorAll(".filter-chip")
    for i in range(chips.length):
        chips[i].addEventListener("click", make_filter_handler(chips[i]))

    search = document.getElementById("search-input")
    search.addEventListener("input", create_proxy(on_search))

asyncio.ensure_future(load_events())

# ── Рендер списка карточек ───────────────────────────────
def render_cards(rows):
    event_list = document.getElementById("event-list")
    event_list.innerHTML = ""
    for row in rows:
        event_list.insertAdjacentHTML("beforeend", build_card_html(row))
    cards = document.querySelectorAll(".event-card")
    for i in range(cards.length):
        cards[i].addEventListener("click", make_card_handler(cards[i]))

# ── Текущий активный фильтр ──────────────────────────────
active_filter = ["all"]

def apply_filters():
    query = document.getElementById("search-input").value.lower().strip()
    tag   = active_filter[0]
    filtered = []
    for row in all_rows:
        tags = [t.strip().lower() for t in row.get("tags","").split("|")]
        if tag != "all" and tag.lower() not in tags:
            continue
        if query:
            haystack = " ".join([
                row.get("title",""),
                row.get("author",""),
                row.get("tags",""),
                row.get("place",""),
            ]).lower()
            if query not in haystack:
                continue
        filtered.append(row)
    render_cards(filtered)

# ── Хендлер фильтр-чипа ──────────────────────────────────
def make_filter_handler(chip):
    def handler(event):
        chips = document.querySelectorAll(".filter-chip")
        for i in range(chips.length):
            chips[i].classList.remove("active")
        chip.classList.add("active")
        active_filter[0] = chip.getAttribute("data-tag")
        apply_filters()
    return create_proxy(handler)

# ── Хендлер поиска ───────────────────────────────────────
def on_search(event):
    apply_filters()

# ── Открываем panel-1 сразу ──────────────────────────────
document.getElementById("panel-1").classList.add("open")
document.getElementById("btn-1").classList.add("active")
document.querySelector("body").classList.add("panel-1-open")
current_open[0] = "panel-1"

# ── Геолокация ───────────────────────────────────────────
def on_location(position):
    lat = position.coords.latitude
    lng = position.coords.longitude
    my_location[0] = (lat, lng)

    my_icon_options = js.Object.new()
    my_icon_options.className = ""
    my_icon_options.html = (
        '<div style="width:14px;height:14px;background:#ff4a4a;'
        'border-radius:50%;border:3px solid #fff;'
        'box-shadow:0 2px 8px rgba(255,74,74,0.6);"></div>'
    )
    my_icon_options.iconSize   = to_js([14, 14])
    my_icon_options.iconAnchor = to_js([7, 7])
    my_icon = js.L.divIcon(my_icon_options)

    marker_opts = js.Object.new()
    marker_opts.icon = my_icon
    marker = js.L.marker(to_js([lat, lng]), marker_opts)
    marker.addTo(leaflet_map)
    marker.bindPopup('<span style="font-weight:600;font-size:13px">Я здесь</span>')
    marker.openPopup()
    leaflet_map.setView(to_js([lat, lng]), 13)

def on_error(error):
    # геолокация недоступна — используем координаты вручную
    my_location[0] = (MY_LAT, MY_LNG)
    leaflet_map.setView(to_js([MY_LAT, MY_LNG]), 13)

js.navigator.geolocation.getCurrentPosition(
    create_proxy(on_location),
    create_proxy(on_error)
)