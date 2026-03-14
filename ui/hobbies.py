import io, csv, js
from pyscript import document
from pyodide.ffi import create_proxy, to_js
import asyncio

async def load_hobbies():
    response = await js.fetch("hobbies.csv")
    buf      = await response.arrayBuffer()
    text     = js.TextDecoder.new("utf-8").decode(buf)
    reader   = csv.DictReader(io.StringIO(text))
    grid     = document.getElementById("hobbies-grid")

    def make_toggle(chip):
        def handler(e):
            chip.classList.toggle("active")
        return create_proxy(handler)

    for row in reader:
        grid.insertAdjacentHTML(
            "beforeend",
            f'<div class="filter-chip" data-id="{row["id"]}">{row["label"]}</div>'
        )

    chips = document.querySelectorAll("#hobbies-grid .filter-chip")
    for i in range(chips.length):
        chips[i].addEventListener("click", make_toggle(chips[i]))

asyncio.ensure_future(load_hobbies())
