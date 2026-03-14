# -*- coding: utf-8 -*-
"""
Runs a localhost HTTP server (serves HTML from bin/ and GET /data.json from the
watched file) and a WebSocket server that notifies clients when the file changes.
Pages load from http://localhost:HTTP_PORT and fetch /data.json; D3 displays the data.
"""

import asyncio
import json
from pathlib import Path

import aiohttp.web
import websockets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

JSON_PATH = Path(r"C:\Users\hackathon\Desktop\Typology_3.json")
HTTP_HOST = "localhost"
HTTP_PORT = 8080
WS_HOST = "localhost"
WS_PORT = 8765

# Path to bin/ (static files)
BIN_DIR = Path(__file__).resolve().parent.parent / "bin"

# All connected WebSocket clients (notify on file change)
clients = set()


async def broadcast_changed():
    """Notify all clients that the JSON file changed (they should refetch /data.json)."""
    if not clients:
        return
    payload = json.dumps({"type": "changed"})
    dead = set()
    for ws in clients:
        try:
            await ws.send(payload)
        except Exception:
            dead.add(ws)
    clients.difference_update(dead)


def make_file_handler(loop):
    """On file change, notify WebSocket clients so they refetch."""

    class Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            path = Path(event.src_path).resolve()
            if path == JSON_PATH.resolve():
                asyncio.run_coroutine_threadsafe(broadcast_changed(), loop)

    return Handler()


async def data_json(request):
    """GET /data.json — return the watched JSON file (for fetch() from the HTML)."""
    try:
        if not JSON_PATH.exists():
            return aiohttp.web.json_response({"error": "File not found"}, status=404)
        text = JSON_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        return aiohttp.web.json_response(data)
    except (json.JSONDecodeError, OSError) as e:
        return aiohttp.web.json_response({"error": str(e)}, status=500)


async def ws_handler(websocket):
    """Register client; send {"type":"changed"} when file changes (client refetches /data.json)."""
    clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        clients.discard(websocket)


@aiohttp.web.middleware
async def cors_middleware(request, handler):
    """Add CORS for static and data so pages loaded from file:// can fetch."""
    resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


def run_http_app():
    """Create and return aiohttp app: static from bin/ + /data.json."""
    app = aiohttp.web.Application(middlewares=[cors_middleware])
    app.router.add_get("/data.json", data_json)
    app.router.add_static("/", BIN_DIR, name="static", show_index=True)
    return app


async def main():
    loop = asyncio.get_running_loop()
    observer = Observer()
    observer.schedule(make_file_handler(loop), str(JSON_PATH.parent), recursive=False)
    observer.start()

    # HTTP server: HTML + /data.json
    app = run_http_app()
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, HTTP_HOST, HTTP_PORT)
    await site.start()
    print("HTTP server: http://{}:{}/  (e.g. /ws_treemap.html, /ws_data.html)".format(HTTP_HOST, HTTP_PORT))
    print("JSON endpoint: http://{}:{}/data.json".format(HTTP_HOST, HTTP_PORT))
    print("WebSocket: ws://{}:{}  (notify on file change)".format(WS_HOST, WS_PORT))
    print("Watching: {}".format(JSON_PATH))

    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
