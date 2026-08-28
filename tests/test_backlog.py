import re

from fastapi.testclient import TestClient

from app.main import app


def csrf(client, path):
    response = client.get(path)
    match = re.search(r'name="csrf" value="([^"]+)"', response.text)
    assert match
    return match.group(1)


def setup_project(email: str) -> TestClient:
    client = TestClient(app)
    client.post("/signup", data={"csrf": csrf(client, "/signup"), "full_name": "Owner", "email": email, "password": "SecurePass123", "confirm_password": "SecurePass123", "mobile": "", "organization_name": ""})
    client.post("/settings/workspace", data={"csrf": csrf(client, "/settings/workspace"), "name": "Workspace", "timezone": "UTC"})
    client.post("/settings/projects", data={"csrf": csrf(client, "/settings/projects"), "name": "Payments", "project_key": "PAY", "description": "", "status": "Active"})
    return client


def test_backlog_crud_readiness_and_archive() -> None:
    client = setup_project("backlog-owner@example.com")
    response = client.post("/backlog", data={"csrf": csrf(client, "/backlog"), "type": "Story", "title": "Process payment", "description": "", "acceptance_criteria": "", "priority": "High", "story_points": "13", "status": "Backlog", "assignee_id": ""}, follow_redirects=False)
    assert response.status_code == 303
    detail_url = response.headers["location"]
    detail = client.get(detail_url)
    assert "PAY-1" in detail.text
    assert "Missing acceptance criteria" in detail.text
    assert "Appears oversized" in detail.text
    response = client.post(detail_url, data={"csrf": csrf(client, detail_url), "type": "Story", "title": "Process card payment", "description": "Details", "acceptance_criteria": "Given a card, payment succeeds", "priority": "High", "story_points": "5", "status": "Ready", "assignee_id": ""}, follow_redirects=False)
    assert response.status_code == 303
    assert "Process card payment" in client.get("/backlog").text
    item_id = detail_url.rsplit("/", 1)[-1]
    response = client.post(f"/backlog/{item_id}/archive", data={"csrf": csrf(client, detail_url)}, follow_redirects=False)
    assert response.status_code == 303
    assert "Process card payment" not in client.get("/backlog").text


def test_backlog_requires_authorized_project() -> None:
    client = TestClient(app)
    client.post("/signup", data={"csrf": csrf(client, "/signup"), "full_name": "No Project", "email": "no-project@example.com", "password": "SecurePass123", "confirm_password": "SecurePass123", "mobile": "", "organization_name": ""})
    assert client.get("/backlog").status_code == 403
