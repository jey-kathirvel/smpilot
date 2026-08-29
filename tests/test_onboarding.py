from fastapi.testclient import TestClient

from app.main import app
from tests import test_auth as _test_auth  # noqa: F401
from tests.test_auth import csrf, signup


def test_new_user_has_visible_workspace_to_project_path():
    client = TestClient(app)
    assert signup(client, "onboarding@example.com").status_code == 303
    projects = client.get("/settings/projects")
    assert projects.status_code == 200
    assert 'href="/settings/workspace"' in projects.text
    assert "Create your first workspace" in client.get("/settings/workspace").text
    response = client.post("/settings/workspace", data={"csrf": csrf(client, "/settings/workspace"), "name": "Onboarding Workspace", "timezone": "Asia/Kolkata"}, follow_redirects=False)
    assert response.status_code == 303
    assert "Continue to projects" in client.get("/settings/workspace").text
    assert "Create your first project" in client.get("/settings/projects").text


def test_project_pages_redirect_unconfigured_user_to_workspace_setup():
    client = TestClient(app)
    assert signup(client, "onboarding-redirect@example.com").status_code == 303
    response = client.get("/backlog", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/settings/workspace"
