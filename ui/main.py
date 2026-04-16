import json as pyjson

import io, csv, js
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

# ── Геолокация ────────────────────────────────────────────
user_icon_opts = js.Object.new()
user_icon_opts.className = ""
user_icon_opts.html = (
    '<div style="'
    'width:16px;height:16px;'
    'background:#ff4d6d;'
    'border-radius:50%;'
    'border:3px solid #fff;'
    'box-shadow:0 0 0 5px rgba(255,77,109,0.22),0 2px 8px rgba(255,77,109,0.5);'
    '"></div>'
)
user_icon_opts.iconSize   = to_js([16, 16])
user_icon_opts.iconAnchor = to_js([8, 8])
user_icon  = js.L.divIcon(user_icon_opts)
user_marker = [None]

def on_location(e):
    if user_marker[0] is not None:
        user_marker[0].remove()
    u_opts = js.Object.new()
    u_opts.icon = user_icon
    m = js.L.marker(to_js([e.latlng.lat, e.latlng.lng]), u_opts)
    m.addTo(leaflet_map)
    user_marker[0] = m

leaflet_map.addEventListener("locationfound", create_proxy(on_location))
locate_opts = js.Object.new()
locate_opts.watch              = True
locate_opts.enableHighAccuracy = True
leaflet_map.locate(locate_opts)

# ── Маркер события ────────────────────────────────────────
def make_event_icon():
    opts = js.Object.new()
    opts.className = ""
    opts.html = (
        '<div style="width:14px;height:14px;background:#4a8cff;'
        'border-radius:50%;border:3px solid #fff;'
        'box-shadow:0 2px 8px rgba(74,140,255,0.6);"></div>'
    )
    opts.iconSize   = to_js([14, 14])
    opts.iconAnchor = to_js([7, 7])
    return js.L.divIcon(opts)

current_markers = {}
current_route   = [None]

# ── Маршрут через polyline (без Routing Machine) ─────────
# Routing Machine нестабилен из Pyodide — используем
# прямую линию + OSRM fetch для реального маршрута

async def draw_route(lat1, lng1, lat2, lng2):
    # убираем старый маршрут
    if current_route[0] is not None:
        current_route[0].remove()
        current_route[0] = None

    # запрашиваем маршрут у OSRM
    url = (
        f"https://router.project-osrm.org/route/v1/foot/"
        f"{lng1},{lat1};{lng2},{lat2}"
        f"?overview=full&geometries=geojson"
    )
    try:
        resp = await js.fetch(url)
        data_text = await resp.text()
        # парсим JSON через js
        data = js.JSON.parse(data_text)
        coords_js = data.routes[0].geometry.coordinates
        # конвертируем [[lng,lat],...] → [[lat,lng],...]
        coords_py = []
        for i in range(coords_js.length):
            c = coords_js[i]
            coords_py.append([c[1], c[0]])

        line_opts = js.Object.new()
        line_opts.color   = "#4a8cff"
        line_opts.weight  = 4
        line_opts.opacity = 0.85
        polyline = js.L.polyline(to_js(coords_py), line_opts)
        polyline.addTo(leaflet_map)
        current_route[0] = polyline

    except Exception as ex:
        # fallback — прямая линия
        line_opts = js.Object.new()
        line_opts.color   = "#4a8cff"
        line_opts.weight  = 4
        line_opts.opacity = 0.6
        line_opts.dashArray = "8 6"
        polyline = js.L.polyline(to_js([[lat1, lng1], [lat2, lng2]]), line_opts)
        polyline.addTo(leaflet_map)
        current_route[0] = polyline

# ── Перелёт камеры ────────────────────────────────────────
def fly_to(lat, lng, lat2=None, lng2=None):
    leaflet_map.invalidateSize()
    ui_px = 52 + 390
    zoom  = 13

    if lat2 and lng2:
        bounds   = js.L.latLngBounds(to_js([[lat, lng], [lat2, lng2]]))
        fit_opts = js.Object.new()
        fit_opts.paddingTopLeft     = to_js([ui_px + 20, 60])
        fit_opts.paddingBottomRight = to_js([60, 60])
        fit_opts.maxZoom            = 14
        leaflet_map.fitBounds(bounds, fit_opts)
        asyncio.ensure_future(draw_route(lat, lng, lat2, lng2))
    else:
        # убираем старый маршрут если был
        if current_route[0] is not None:
            current_route[0].remove()
            current_route[0] = None
        pt      = leaflet_map.project(to_js([lat, lng]), zoom)
        shifted = js.L.point(pt.x - ui_px / 2, pt.y)
        center  = leaflet_map.unproject(shifted, zoom)
        fly_opts = js.Object.new()
        fly_opts.duration = 1.0
        leaflet_map.flyTo(center, zoom, fly_opts)

# ── Панели ────────────────────────────────────────────────
panels  = ["panel-1", "panel-2", "panel-3", "panel-4"]
buttons = ["btn-1",   "btn-2",   "btn-3",   "btn-4"  ]
current_open = [None]

def open_panel(panel_id, btn_id):
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

def make_toggle(panel_id, btn_id):
    def handler(event):
        if current_open[0] == panel_id:
            return
        open_panel(panel_id, btn_id)
    return create_proxy(handler)

for p, b in zip(panels, buttons):
    document.getElementById(b).addEventListener("click", make_toggle(p, b))

# ── Карточка HTML ─────────────────────────────────────────
def build_card_html(row):
    participants_html = ""
    for name in row.get("participants", "").split("|"):
        name = name.strip()
        if name:
            participants_html += f"""
            <div class="participant">
              <div class="participant-avatar"></div>
              <span class="participant-name">{name}</span>
            </div>"""

    has_route = row.get("lat2","").strip() and row.get("lng2","").strip()
    route_badge = (
        '<div class="filter-chip active" style="font-size:10px;padding:2px 9px;'
        'margin-top:6px;display:inline-flex;gap:4px;">A → B маршрут</div>'
    ) if has_route else ""

    return f"""
    <li class="event-card"
        data-id="{row['id'].strip()}"
        data-lat="{row['lat'].strip()}"
        data-lng="{row['lng'].strip()}"
        data-lat2="{row.get('lat2','').strip()}"
        data-lng2="{row.get('lng2','').strip()}"
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
        {route_badge}
      </div>
      <div class="event-expandable">
        <p class="event-desc">{row['desc'].strip()}</p>
        <div class="event-participants">{participants_html}</div>
        <button class="btn-join">join</button>
      </div>
    </li>"""

# ── Выбор карточки ────────────────────────────────────────
def select_card(event_id):
    all_cards = document.querySelectorAll(".event-card")
    for i in range(all_cards.length):
        card = all_cards[i]
        if card.getAttribute("data-id") == str(event_id):
            card.classList.add("selected")
            card.scrollIntoView(to_js({"behavior": "smooth", "block": "nearest"}))
        else:
            card.classList.remove("selected")

def make_card_handler(card):
    def handler(event):
        if event.target.classList.contains("btn-join"):
            return
        eid    = card.getAttribute("data-id")
        lat    = float(card.getAttribute("data-lat"))
        lng    = float(card.getAttribute("data-lng"))
        lat2_s = card.getAttribute("data-lat2")
        lng2_s = card.getAttribute("data-lng2")
        lat2   = float(lat2_s) if lat2_s else None
        lng2   = float(lng2_s) if lng2_s else None
        select_card(eid)
        fly_to(lat, lng, lat2, lng2)
    return create_proxy(handler)

def make_marker_click(event_id, lat, lng, lat2, lng2):
    def handler(e):
        if current_open[0] != "panel-1":
            open_panel("panel-1", "btn-1")
        select_card(event_id)
        fly_to(lat, lng, lat2, lng2)
    return create_proxy(handler)

# ── Загрузка CSV ──────────────────────────────────────────
all_rows = []

async def load_events():
    response = await js.fetch("/static/events.csv")
    buf      = await response.arrayBuffer()
    text     = js.TextDecoder.new("utf-8").decode(buf)
    reader   = csv.DictReader(io.StringIO(text))
    rows     = list(reader)
    all_rows.extend(rows)
    render_cards(rows)
    place_markers(rows)

    seen     = set()
    dropdown = document.getElementById("filter-dropdown")
    for row in rows:
        for tag in row.get("tags","").split("|"):
            tag = tag.strip()
            if tag and tag not in seen:
                seen.add(tag)
                dropdown.insertAdjacentHTML(
                    "beforeend",
                    f'<div class="filter-chip" data-tag="{tag}">{tag}</div>'
                )

    chips = document.querySelectorAll("#filter-dropdown .filter-chip")
    for i in range(chips.length):
        chips[i].addEventListener("click", make_filter_handler(chips[i]))

    document.getElementById("search-input").addEventListener(
        "input", create_proxy(on_search)
    )
    document.getElementById("filter-toggle").addEventListener(
        "click", create_proxy(on_filter_toggle)
    )

asyncio.ensure_future(load_events())

def place_markers(rows):
    icon = make_event_icon()
    for row in rows:
        try:
            lat = float(row['lat'].strip())
            lng = float(row['lng'].strip())
        except:
            continue
        lat2_s = row.get('lat2','').strip()
        lng2_s = row.get('lng2','').strip()
        lat2   = float(lat2_s) if lat2_s else None
        lng2   = float(lng2_s) if lng2_s else None

        mk_opts      = js.Object.new()
        mk_opts.icon = icon
        marker       = js.L.marker(to_js([lat, lng]), mk_opts)
        marker.addTo(leaflet_map)
        marker.addEventListener(
            "click",
            make_marker_click(row['id'].strip(), lat, lng, lat2, lng2)
        )
        current_markers[row['id'].strip()] = marker

def render_cards(rows):
    event_list           = document.getElementById("event-list")
    event_list.innerHTML = ""
    for row in rows:
        event_list.insertAdjacentHTML("beforeend", build_card_html(row))
    cards = document.querySelectorAll(".event-card")
    for i in range(cards.length):
        cards[i].addEventListener("click", make_card_handler(cards[i]))

# ── Дропдаун ─────────────────────────────────────────────
dropdown_open  = [False]
active_filter  = ["all"]

def on_filter_toggle(event):
    dropdown = document.getElementById("filter-dropdown")
    btn      = document.getElementById("filter-toggle")
    dropdown_open[0] = not dropdown_open[0]
    if dropdown_open[0]:
        dropdown.classList.add("open")
        btn.classList.add("active")
    else:
        dropdown.classList.remove("open")
        btn.classList.remove("active")

def make_filter_handler(chip):
    def handler(event):
        chips = document.querySelectorAll("#filter-dropdown .filter-chip")
        for i in range(chips.length):
            chips[i].classList.remove("active")
        chip.classList.add("active")
        active_filter[0] = chip.getAttribute("data-tag")
        document.getElementById("filter-dropdown").classList.remove("open")
        document.getElementById("filter-toggle").classList.remove("active")
        dropdown_open[0] = False
        document.getElementById("filter-label").textContent = chip.textContent
        apply_filters()
    return create_proxy(handler)

def on_search(event):
    apply_filters()

def apply_filters():
    query    = document.getElementById("search-input").value.lower().strip()
    tag      = active_filter[0]
    filtered = []
    for row in all_rows:
        tags = [t.strip().lower() for t in row.get("tags","").split("|")]
        if tag != "all" and tag.lower() not in tags:
            continue
        if query:
            haystack = " ".join([
                row.get("title",""), row.get("author",""),
                row.get("tags",""),  row.get("place",""),
            ]).lower()
            if query not in haystack:
                continue
        filtered.append(row)
    render_cards(filtered)

# ── Старт ─────────────────────────────────────────────────
open_panel("panel-1", "btn-1")

# ── Создание мероприятия ──────────────────────────────────
new_event_id = [100]  # локальный счётчик id

def get_val(el_id):
    return document.getElementById(el_id).value.strip()

def show_hint(msg, kind=""):
    hint = document.getElementById("create-hint")
    hint.textContent = msg
    hint.className = f"create-hint {kind}"

def on_create(event):
    title      = get_val("new-title")
    author     = get_val("new-author")
    tags       = get_val("new-tags")
    time_start = get_val("new-time-start")
    time_end   = get_val("new-time-end")
    place      = get_val("new-place")
    desc       = get_val("new-desc")
    lat_s      = get_val("new-lat")
    lng_s      = get_val("new-lng")
    lat2_s     = get_val("new-lat2")
    lng2_s     = get_val("new-lng2")

    # валидация
    if not title:
        show_hint("Введи название", "error"); return
    if not lat_s or not lng_s:
        show_hint("Укажи координаты точки А", "error"); return
    try:
        lat = float(lat_s); lng = float(lng_s)
    except:
        show_hint("Неверные координаты точки А", "error"); return

    lat2 = lng2 = None
    if lat2_s or lng2_s:
        try:
            lat2 = float(lat2_s); lng2 = float(lng2_s)
        except:
            show_hint("Неверные координаты точки B", "error"); return

    new_event_id[0] += 1
    eid = str(new_event_id[0])

    new_row = {
        "id":         eid,
        "title":      title,
        "author":     author or "Аноним",
        "tags":       tags or "other",
        "time_start": time_start or "—",
        "time_end":   time_end or "—",
        "place":      place or "—",
        "lat":        str(lat),
        "lng":        str(lng),
        "lat2":       str(lat2) if lat2 else "",
        "lng2":       str(lng2) if lng2 else "",
        "desc":       desc,
        "participants": "",
    }

    # добавляем в общий список
    all_rows.append(new_row)

    # рендерим карточку в список
    event_list = document.getElementById("event-list")
    event_list.insertAdjacentHTML("beforeend", build_card_html(new_row))

    # вешаем хендлер на новую карточку
    new_card = event_list.querySelector(f'[data-id="{eid}"]')
    new_card.addEventListener("click", make_card_handler(new_card))

    # ставим маркер на карту
    icon = make_event_icon()
    mk_opts = js.Object.new()
    mk_opts.icon = icon
    marker = js.L.marker(to_js([lat, lng]), mk_opts)
    marker.addTo(leaflet_map)
    marker.addEventListener(
        "click",
        make_marker_click(eid, lat, lng, lat2, lng2)
    )
    current_markers[eid] = marker

    # летим к новому мероприятию
    open_panel("panel-1", "btn-1")
    select_card(eid)
    fly_to(lat, lng, lat2, lng2)

    # очищаем форму
    for fid in ["new-title","new-author","new-tags","new-time-start",
                "new-time-end","new-place","new-desc",
                "new-lat","new-lng","new-lat2","new-lng2"]:
        document.getElementById(fid).value = ""

    show_hint(f"«{title}» добавлено!", "success")

document.getElementById("btn-create").addEventListener("click", create_proxy(on_create))



# ── Чат ──────────────────────────────────────────────────

chat_session_id = [None]
all_sessions = []

def add_message(text, role, anchor_id=None, is_summary=False):
    messages_el = document.getElementById("chat-messages")
    div = document.createElement("div")
    cls = "chat-msg chat-msg--" + ("user" if role == "user" else "bot")
    if is_summary:
        cls += " chat-msg--summary"
    div.className = cls

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip():
            span = document.createElement("span")
            span.textContent = line
            div.appendChild(span)
        if i < len(lines) - 1:
            div.appendChild(document.createElement("br"))

    if anchor_id:
        div.id = anchor_id
    messages_el.appendChild(div)
    messages_el.scrollTop = messages_el.scrollHeight

def add_typing():
    messages_el = document.getElementById("chat-messages")
    div = document.createElement("div")
    div.className = "chat-msg chat-msg--bot"
    div.id = "typing-indicator"
    div.textContent = "..."
    messages_el.appendChild(div)
    messages_el.scrollTop = messages_el.scrollHeight

def remove_typing():
    t = document.getElementById("typing-indicator")
    if t:
        t.remove()

def add_session_divider(session_id, label):
    messages_el = document.getElementById("chat-messages")
    div = document.createElement("div")
    div.className = "chat-session-divider"
    div.id = f"session-anchor-{session_id}"
    inner = document.createElement("span")
    inner.className = "chat-session-divider-label"
    inner.textContent = label
    div.appendChild(inner)
    messages_el.appendChild(div)

def render_sessions_sidebar():
    sidebar = document.getElementById("chat-sessions-list")
    sidebar.innerHTML = ""


    for s in reversed(all_sessions):
        item = document.createElement("div")
        item.className = "chat-session-item" + (" active" if s["id"] == chat_session_id[0] else "")
        item.setAttribute("data-sid", str(s["id"]))

        date_div = document.createElement("div")
        date_div.className = "session-date"
        date_div.textContent = s.get("date", "—")
        item.appendChild(date_div)

        title_div = document.createElement("div")
        title_div.textContent = s.get("title", f"Диалог {s['id']}")
        item.appendChild(title_div)

        sid = s["id"]
        concluded = s.get("concluded", False)
        item.addEventListener("click", create_proxy(make_session_click(sid, concluded)))
        sidebar.appendChild(item)

def make_session_click(sid, concluded):
    def handler(e):
        anchor = document.getElementById(f"session-anchor-{sid}")
        if anchor:
            anchor.scrollIntoView(to_js({"behavior": "smooth", "block": "start"}))
        # переключаем активную только если не завершена
        if not concluded:
            chat_session_id[0] = sid
        items = document.querySelectorAll(".chat-session-item")
        for i in range(items.length):
            items[i].classList.remove("active")
            if items[i].getAttribute("data-sid") == str(sid):
                items[i].classList.add("active")
    return handler

async def load_session_messages(sid, is_concluded=False):
    try:
        resp = await js.fetch(f"/chat/api/sessions/{sid}/")
        data_text = await resp.text()
        data = js.JSON.parse(data_text)
        messages_js = data.messages
        for i in range(messages_js.length):
            m = messages_js[i]
            # последнее сообщение ассистента в завершённой сессии — summary
            is_last = (i == messages_js.length - 1)
            is_sum = is_concluded and m.role == "assistant" and is_last
            add_message(m.content, m.role, is_summary=is_sum)
    except Exception as e:
        pass

async def load_all_history():
    messages_el = document.getElementById("chat-messages")
    messages_el.innerHTML = ""
    for s in all_sessions:
        sid = s["id"]
        label = s.get("date", f"Диалог {sid}")
        if s.get("concluded"):
            label += " ✓"
        add_session_divider(sid, label)
        await load_session_messages(sid, is_concluded=s.get("concluded", False))
    messages_el = document.getElementById("chat-messages")
    messages_el.scrollTop = messages_el.scrollHeight

async def create_session():
    fetch_opts = to_js({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
    }, dict_converter=js.Object.fromEntries)

    resp = await js.fetch("/chat/api/sessions/", fetch_opts)
    data_text = await resp.text()
    data = js.JSON.parse(data_text)
    sid = data.session.id
    chat_session_id[0] = sid

    today = js.Date.new().toLocaleDateString("ru-RU")
    all_sessions.append({
        "id": sid,
        "title": "Новый диалог",
        "date": today,
        "concluded": False,
    })

    add_session_divider(sid, today)
    add_message("Привет! Как ты себя чувствуешь сегодня?", "bot")
    render_sessions_sidebar()

async def start_new_session():
    await create_session()

async def send_chat(conclude=False):
    if chat_session_id[0] is None:
        await create_session()

    # проверяем что текущая сессия не завершена
    current_concluded = False
    for s in all_sessions:
        if s["id"] == chat_session_id[0]:
            current_concluded = s.get("concluded", False)
            break

    if current_concluded and not conclude:
        await create_session()

    input_el = document.getElementById("chat-input")
    text = input_el.value.strip()

    if not text and not conclude:
        return

    if not conclude:
        add_message(text, "user")
        input_el.value = ""

    add_typing()

    try:
        sid = chat_session_id[0]

        if conclude:
            url = f"/chat/api/sessions/{sid}/conclude/"
            fetch_opts = to_js({
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": pyjson.dumps({})
            }, dict_converter=js.Object.fromEntries)
        else:
            url = f"/chat/api/sessions/{sid}/send/"
            fetch_opts = to_js({
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": pyjson.dumps({"content": text})
            }, dict_converter=js.Object.fromEntries)

        resp = await js.fetch(url, fetch_opts)
        data_text = await resp.text()

        if not data_text.strip():
            remove_typing()
            add_message("Сервер вернул пустой ответ.", "bot")
            return

        data = js.JSON.parse(data_text)
        remove_typing()

        if conclude:
            reply = data.conclusion if hasattr(data, "conclusion") else "..."
            add_message(reply, "bot", is_summary=True)
            for s in all_sessions:
                if s["id"] == sid:
                    s["concluded"] = True
                    short = reply.replace("\n", " ")[:35]
                    if len(reply) > 35:
                        short += "..."
                    s["title"] = "✓ " + short
            render_sessions_sidebar()
        else:
            reply = data.bot_message.content if hasattr(data, "bot_message") else "..."
            add_message(reply, "bot")

    except Exception as e:
        remove_typing()
        add_message(f"Ошибка: {str(e)}", "bot")

async def load_session_titles():
    for s in all_sessions:
        try:
            resp = await js.fetch(f"/chat/api/sessions/{s['id']}/")
            data_text = await resp.text()
            data = js.JSON.parse(data_text)
            messages_js = data.messages
            for i in range(messages_js.length):
                m = messages_js[i]
                if m.role == "user":
                    content = str(m.content)
                    title = content[:35] + ("..." if len(content) > 35 else "")
                    s["title"] = ("✓ " if s.get("concluded") else "") + title
                    break
        except Exception:
            pass

async def init_chat():
    try:
        resp = await js.fetch("/chat/api/sessions/")
        data_text = await resp.text()
        data = js.JSON.parse(data_text)
        sessions_js = data.sessions
        all_sessions.clear()
        for i in range(sessions_js.length):
            s = sessions_js[i]
            sid = s.id
            created = str(s.created_at)[:10] if hasattr(s, "created_at") else ""
            concluded = s.concluded if hasattr(s, "concluded") else False
            all_sessions.append({
                "id": sid,
                "title": f"Диалог {sid}",
                "date": created,
                "concluded": concluded,
            })
        await load_session_titles()
        render_sessions_sidebar()
    except Exception as e:
        pass

    if all_sessions:
        await load_all_history()
        # активная — последняя незавершённая
        for s in reversed(all_sessions):
            if not s.get("concluded"):
                chat_session_id[0] = s["id"]
                break
        if chat_session_id[0] is None:
            await create_session()
        render_sessions_sidebar()
    else:
        await create_session()

def on_send_click(event):
    asyncio.ensure_future(send_chat(False))

def on_end_click(event):
    asyncio.ensure_future(send_chat(True))

def on_keydown(event):
    if event.key == "Enter" and not event.shiftKey:
        event.preventDefault()
        asyncio.ensure_future(send_chat(False))

asyncio.ensure_future(init_chat())

document.getElementById("chat-send").addEventListener("click", create_proxy(on_send_click))
document.getElementById("chat-end").addEventListener("click", create_proxy(on_end_click))
document.getElementById("chat-input").addEventListener("keydown", create_proxy(on_keydown))