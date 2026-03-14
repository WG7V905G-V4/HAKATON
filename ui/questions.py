import io, csv, js
from pyscript import document
from pyodide.ffi import create_proxy, to_js
import asyncio

async def load_questions():
    response = await js.fetch("questions.csv")
    buf      = await response.arrayBuffer()
    text     = js.TextDecoder.new("utf-8").decode(buf)
    reader   = csv.DictReader(io.StringIO(text))
    lst      = document.getElementById("questions-list")

    def make_single_select(block):
        def handler(e):
            chips = block.querySelectorAll(".filter-chip")
            for i in range(chips.length):
                chips[i].classList.remove("active")
            e.target.classList.add("active")
        return create_proxy(handler)

    for row in reader:
        answers_html = "".join(
            f'<div class="filter-chip">{row[k]}</div>'
            for k in ["a1","a2","a3","a4"] if row.get(k,"").strip()
        )
        lst.insertAdjacentHTML("beforeend", f"""
        <li class="event-card">
          <div class="event-main">
            <div class="event-title">{row["question"]}</div>
          </div>
          <div class="event-expandable" style="max-height:none;opacity:1;padding-bottom:14px;">
            <div class="filter-bar" style="flex-direction:column;">
              {answers_html}
            </div>
          </div>
        </li>""")

    blocks = document.querySelectorAll("#questions-list .event-card")
    for i in range(blocks.length):
        handler = make_single_select(blocks[i])
        chips = blocks[i].querySelectorAll(".filter-chip")
        for j in range(chips.length):
            chips[j].addEventListener("click", handler)

asyncio.ensure_future(load_questions())
