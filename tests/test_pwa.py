from fastapi.testclient import TestClient

from app.main import app


def test_pwa_files():
    client = TestClient(app)
    manifest = client.get("/manifest.json")
    assert manifest.status_code == 200
    data = manifest.json()
    assert data["display"] == "standalone"
    assert data["start_url"] == "/today"
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    assert {icon["sizes"] for icon in data["icons"]} == {"192x192", "512x512"}
    worker = client.get("/service-worker.js")
    assert worker.status_code == 200
    assert worker.headers["service-worker-allowed"] == "/"
    assert "event.request.method !== 'GET'" in worker.text
    assert "smpilot-shell-v2" in worker.text
    assert "fetch(event.request)" in worker.text
    assert "caches.match(event.request)" in worker.text
    assert worker.text.index("fetch(event.request)") < worker.text.index("caches.match(event.request)")
    offline = client.get("/static/offline.html")
    assert offline.status_code == 200
    assert "You're offline." in offline.text
    assert "Reconnect to update sprint information." in offline.text


def test_ui_assets_revalidate_and_are_cache_busted():
    client = TestClient(app)
    login = client.get("/login")
    assert "/static/css/app.css?v=" in login.text
    assert "/static/js/app.js?v=" in login.text
    assert client.get("/static/css/app.css").headers["cache-control"] == "no-cache, must-revalidate"
    assert client.get("/static/js/app.js").headers["cache-control"] == "no-cache, must-revalidate"
