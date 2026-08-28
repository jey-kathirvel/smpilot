from fastapi.testclient import TestClient

from app.main import app


def test_pwa_files():
    client = TestClient(app)
    manifest = client.get("/static/manifest.json")
    assert manifest.status_code == 200
    data = manifest.json()
    assert data["display"] == "standalone"
    assert data["start_url"] == "/today"
    assert {icon["sizes"] for icon in data["icons"]} == {"192x192", "512x512"}
    worker = client.get("/service-worker.js")
    assert worker.status_code == 200
    assert worker.headers["service-worker-allowed"] == "/"
    assert "event.request.method !== 'GET'" in worker.text
    offline = client.get("/static/offline.html")
    assert offline.status_code == 200
    assert "You're offline." in offline.text
    assert "Reconnect to update sprint information." in offline.text
