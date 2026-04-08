#!/usr/bin/env python3
"""
server.py — Minimal HTTP server that serves all pages and routes API calls.

Usage:
    python server.py

Then open http://localhost:8080/signup.html in your browser.

Routes:
  Static files (.html, .css, .js, .jpg, .png, .csv) → served from current dir
  POST /signup.py   → signup.handle_request
  GET  /hobbies.py  → hobbies.handle_request
  POST /hobbies.py  → hobbies.handle_request
  GET  /questions.py → questions.handle_request
  POST /questions.py → questions.handle_request
  GET  /dashboard.py → dashboard.handle_request
  POST /dashboard.py → dashboard.handle_request
"""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import signup
import hobbies
import questions
import dashboard

PORT = 8080
STATIC_EXTS = {".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".csv"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    # ── Helpers ──────────────────────────────────────────────────
    def _send_json(self, data: dict, status: int = 200, set_cookie: str = ""):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if set_cookie:
            # HttpOnly session cookie, expires in 7 days
            self.send_header(
                "Set-Cookie",
                f"session_token={set_cookie}; Path=/; HttpOnly; Max-Age=604800"
            )
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, path: Path):
        mime, _ = mimetypes.guess_type(str(path))
        mime = mime or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def _cookie(self) -> str:
        return self.headers.get("Cookie", "")

    # ── OPTIONS (CORS preflight) ──────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── GET ───────────────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0]

        # Default route
        if path == "/":
            path = "/signup.html"

        # API endpoints
        if path == "/hobbies.py":
            result = hobbies.handle_request("GET", b"", self._cookie())
            self._send_json(result)
            return

        if path == "/questions.py":
            result = questions.handle_request("GET", b"", self._cookie())
            self._send_json(result)
            return

        if path == "/dashboard.py":
            result = dashboard.handle_request("GET", b"", self._cookie())
            self._send_json(result)
            return

        # Static files
        file_path = Path(".") / path.lstrip("/")
        if file_path.suffix in STATIC_EXTS and file_path.exists():
            self._send_static(file_path)
            return

        self.send_error(404, f"Not found: {path}")

    # ── POST ──────────────────────────────────────────────────────
    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._read_body()
        cookie = self._cookie()

        if path == "/signup.py":
            result, token = signup.handle_request("POST", body, cookie)
            self._send_json(result, set_cookie=token)
            return

        if path == "/hobbies.py":
            result = hobbies.handle_request("POST", body, cookie)
            self._send_json(result)
            return

        if path == "/questions.py":
            result = questions.handle_request("POST", body, cookie)
            self._send_json(result)
            return

        if path == "/dashboard.py":
            result = dashboard.handle_request("POST", body, cookie)
            self._send_json(result)
            return

        self.send_error(404, f"Not found: {path}")


if __name__ == "__main__":
    server = HTTPServer(("", PORT), Handler)
    print(f"✓ Server running at http://localhost:{PORT}/")
    print("  Open http://localhost:{PORT}/signup.html to start.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
