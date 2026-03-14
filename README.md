# Rhino 8 Web Graph Prototype

Minimal Rhino 8 Python setup that opens an Eto popup with a `WebView` to preview chart URLs (for example Flourish embed links).

## Project structure

- `scripts/ui_popup.py` - Eto dialog with WebView; modes:
  - **Flourish URL** – paste/load an embed URL
  - **Animated Treemap (local)** – loads `bin/animated_treemap.html`
  - **Local JSON (treemap)** – D3 treemap from a watched JSON file (via listener)
  - **Local JSON (data only)** – raw JSON from the same connection, no chart
- `scripts/listener.py` - **Localhost server** and file watcher. Run: `python scripts/listener.py`. It:
  - Serves HTML from `bin/` at **http://localhost:8080** (e.g. http://localhost:8080/ws_treemap.html).
  - Serves the watched JSON at **GET http://localhost:8080/data.json** (pages use `fetch('/data.json')` and display with D3).
  - Runs a WebSocket server on **ws://localhost:8765** and sends `{"type":"changed"}` when the file changes so the page can refetch.
  - Watches: `C:\Users\hackathon\Desktop\Typology_3.json`.
- `bin/ws-client.js` - Connects to the WebSocket; on connect fetches `/data.json` and calls `window.onWSData(data)`; on `{"type":"changed"}` refetches and updates. Use in any HTML that needs live JSON (D3 treemap, bar, etc.).
- `bin/ws_data.html` - Uses `ws-client.js`; shows raw JSON (no chart).
- `bin/ws_treemap.html` - Uses `ws-client.js` + D3; draws a treemap (one possible chart).
- `scripts/run_button.py` - Launch script for a Rhino toolbar button.
- `scripts/run_button_animated.py` - Launcher that opens in local animated treemap mode.

## Requirements

- Rhino 8
- RhinoCode CPython (Python 3) runtime
- For local JSON mode: Python with `pip install -r requirements.txt` (aiohttp, websockets, watchdog)
- Public chart URL that allows embedding (Flourish embed links are a common starting point)

## Run from Rhino command line

Use:

`_-RunPythonScript "C:\Users\Matea.Pinjusic\Documents\datacharts\scripts\run_button.py"`

You can also assign the same command to a Rhino toolbar button.

For direct local animated treemap mode:

`_-RunPythonScript "C:\Users\Matea.Pinjusic\Documents\datacharts\scripts\run_button_animated.py"`

## Usage

1. Run `run_button.py` from Rhino.
2. Choose mode (Flourish URL, Animated Treemap, Local JSON treemap, or Local JSON data only).
3. For **Local JSON** modes: run `python scripts/listener.py` first. Then in the dialog choose Local JSON (treemap) or (data only) and load—the WebView opens http://localhost:8080/... and the page fetches /data.json and displays with D3 (or raw). When the JSON file is saved, the server notifies the page and it refetches.
4. In URL mode, paste your chart URL and click **Load URL** (or **Load Treemap** / **Load data** in other modes).
5. Click **Reload** if you need to refresh the page.

## Notes

- Use an actual embed URL, not an editor/share page URL.
- Some websites block embedding via CSP or `X-Frame-Options`; if so, the page may not render inside `WebView`.
- `ui_popup.py` includes a placeholder custom-scheme bridge (`myapp://...`) for JS -> Rhino messages.
- `run_button.py` explicitly checks for CPython and stops with a clear message in IronPython.

## Local JSON and different charts

The flow is: **HTML runs on localhost → fetch /data.json → display with D3**; when the file changes, WebSocket notifies and the page refetches.

1. **listener.py** serves pages at http://localhost:8080 and the JSON at http://localhost:8080/data.json; it watches the JSON file and sends `{"type":"changed"}` over WebSocket when it changes.
2. **ws-client.js** fetches `/data.json` on connect and when the WebSocket says changed, then calls `window.onWSData(data)` so your chart can update.
3. To add another chart: add an HTML file in `bin/`, include `ws-client.js` and D3, and define `window.onWSData = function(data) { ... }` to render it. Add a UI mode that loads http://localhost:8080/your_page.html if you want it in the Rhino dialog.
