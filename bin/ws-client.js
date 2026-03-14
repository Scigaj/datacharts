/**
 * For use when HTML is served from the localhost server (listener.py).
 * Fetches JSON from GET /data.json and notifies the page; subscribes to WebSocket
 * and refetches when the server sends {"type":"changed"} (file changed).
 *
 * - Set window.WS_DATA_FETCH_URL to override the JSON endpoint (default /data.json
 *   when page origin is http://localhost:8080, else http://localhost:8080/data.json).
 */
(function () {
  const WS_URL = "ws://localhost:8765";
  const FETCH_URL = window.WS_DATA_FETCH_URL ||
    (location.origin === "http://localhost:8080" ? "/data.json" : "http://localhost:8080/data.json");
  const RETRY_MS = 3000;

  function statusEl() {
    return document.getElementById("ws-status");
  }
  function setStatus(msg) {
    const el = statusEl();
    if (el) el.textContent = msg;
  }

  function notify(data, error) {
    if (typeof window.onWSData === "function") window.onWSData(data, error);
    window.dispatchEvent(new CustomEvent("ws-data", { detail: { data: data, error: error || null } }));
  }

  async function fetchData() {
    setStatus("Fetching data…");
    try {
      const res = await fetch(FETCH_URL);
      const data = await res.json();
      if (!res.ok) {
        notify(null, data.error || "Request failed");
        setStatus("Error: " + (data.error || res.status));
        return;
      }
      if (data && data.error) {
        notify(null, data.error);
        setStatus("Error: " + data.error);
        return;
      }
      setStatus("Data received. File changes will update automatically.");
      notify(data, null);
    } catch (err) {
      setStatus("Fetch error: " + err.message);
      notify(null, err.message);
    }
  }

  function connect() {
    setStatus("Connecting…");
    const ws = new WebSocket(WS_URL);

    ws.onopen = function () {
      setStatus("Connected. Fetching data…");
      fetchData();
    };

    ws.onmessage = function (ev) {
      try {
        const msg = JSON.parse(ev.data);
        if (msg && msg.type === "changed") {
          setStatus("File changed. Refetching…");
          fetchData();
          return;
        }
        setStatus("Data received.");
        notify(msg, null);
      } catch (_) {
        setStatus("Message parse error.");
      }
    };

    ws.onerror = function () {
      setStatus("WebSocket error. Is listener.py running?");
    };

    ws.onclose = function () {
      setStatus("Disconnected. Retrying in " + RETRY_MS / 1000 + "s…");
      setTimeout(connect, RETRY_MS);
    };
  }

  connect();
})();
