from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_application_has_expected_title() -> None:
    assert app.title == "SMPilot AI"


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "application": "SMPilot AI", "environment": "development"}


def test_login_page() -> None:
    response = client.get("/login")
    assert response.status_code == 200
    assert "Welcome back" in response.text


def test_signup_page() -> None:
    response = client.get("/signup")
    assert response.status_code == 200
    assert "Create your workspace" in response.text


def test_unknown_page_uses_friendly_404() -> None:
    response = client.get("/not-a-real-page")
    assert response.status_code == 404
    assert "Page not found" in response.text
