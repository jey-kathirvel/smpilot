import re

from fastapi.testclient import TestClient

from app.main import app


def csrf(client: TestClient, path: str) -> str:
    response = client.get(path)
    match = re.search(r'name="csrf" value="([^"]+)"', response.text)
    assert match
    return match.group(1)


def register(client: TestClient, email: str) -> None:
    token = csrf(client, "/signup")
    response = client.post("/signup", data={"csrf": token, "full_name": email.split("@")[0], "email": email, "password": "SecurePass123", "confirm_password": "SecurePass123", "mobile": "", "organization_name": ""}, follow_redirects=False)
    assert response.status_code == 303


def test_workspace_project_and_team_flow() -> None:
    client = TestClient(app)
    register(client, "owner@example.com")
    response = client.post("/settings/workspace", data={"csrf": csrf(client, "/settings/workspace"), "name": "Acme", "timezone": "Asia/Kolkata"}, follow_redirects=False)
    assert response.status_code == 303
    response = client.post("/settings/projects", data={"csrf": csrf(client, "/settings/projects"), "name": "Payments", "project_key": "pay", "description": "Payment modernization", "status": "Active"}, follow_redirects=False)
    assert response.status_code == 303
    response = client.post("/team", data={"csrf": csrf(client, "/team"), "display_name": "Ravi", "role": "Developer", "capacity_hours_per_day": "6", "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri"], "active": "true"}, follow_redirects=False)
    assert response.status_code == 303
    assert "Ravi" in client.get("/team").text


def test_unrelated_user_cannot_select_workspace() -> None:
    owner = TestClient(app)
    register(owner, "workspace-owner@example.com")
    owner.post("/settings/workspace", data={"csrf": csrf(owner, "/settings/workspace"), "name": "Private Workspace", "timezone": "UTC"})
    html = owner.get("/settings/workspace").text
    workspace_id = re.search(r'name="workspace_id" value="([^"]+)"', html).group(1)
    outsider = TestClient(app)
    register(outsider, "outsider@example.com")
    response = outsider.post("/settings/workspace/select", data={"csrf": csrf(outsider, "/settings/workspace"), "workspace_id": workspace_id})
    assert response.status_code == 403
