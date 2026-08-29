from app.config import Settings
from tests import test_auth as _test_auth  # noqa: F401
from tests.test_backlog import csrf, setup_project


def test_submit_update_and_generate_daily_summary(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.standup.get_settings", lambda: Settings(openai_api_key="", _env_file=None))
    client = setup_project("standup-owner@example.com")
    response = client.post("/standup", data={"csrf": csrf(client, "/standup"), "yesterday": "Finished checkout", "today": "Test refunds", "blockers": "Waiting for credentials", "confidence": "0.7"}, follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/standup").text
    assert "Finished checkout" in page and "Waiting for credentials" in page
    response = client.post("/standup/summary", data={"csrf": csrf(client, "/standup")}, follow_redirects=False)
    assert response.status_code == 303
    summary = client.get("/standup").text
    assert "1 updates submitted" in summary and "Test refunds" in summary


def test_standup_requires_an_authorized_project() -> None:
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    client.post("/signup", data={"csrf": csrf(client, "/signup"), "full_name": "No Project", "email": "standup-no-project@example.com", "password": "SecurePass123", "confirm_password": "SecurePass123", "mobile": "", "organization_name": ""})
    response = client.get("/standup", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/settings/workspace"
