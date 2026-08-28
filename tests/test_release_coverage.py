import re

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.organization import TeamMember
from tests import test_auth as _test_auth  # noqa: F401
from tests.test_backlog import csrf, setup_project


def selected_project_id(client: TestClient) -> str:
    page = client.get("/settings/projects").text
    match = re.search(r'name="project_id" value="([^"]+)"', page)
    assert match
    return match.group(1)


def test_cross_user_project_and_backlog_object_access_is_denied():
    owner = setup_project("release-owner@example.com")
    owner_project_id = selected_project_id(owner)
    created = owner.post(
        "/backlog",
        data={"csrf": csrf(owner, "/backlog"), "type": "Story", "title": "Private roadmap item", "priority": "High", "story_points": "3", "status": "Backlog"},
        follow_redirects=False,
    )
    assert created.status_code == 303
    private_item_url = created.headers["location"]

    outsider = setup_project("release-outsider@example.com")
    response = outsider.post(
        "/settings/projects/select",
        data={"csrf": csrf(outsider, "/settings/projects"), "project_id": owner_project_id},
    )
    assert response.status_code == 403
    assert outsider.get(private_item_url).status_code == 404
    assert "Private roadmap item" not in outsider.get("/backlog").text


def test_team_member_identifier_cannot_mutate_another_project():
    owner = setup_project("team-owner-release@example.com")
    owner.post(
        "/team",
        data={"csrf": csrf(owner, "/team"), "display_name": "Protected Member", "role": "Developer", "capacity_hours_per_day": "6", "working_days": ["Mon"], "active": "true"},
    )
    session_source = app.dependency_overrides[get_db]()
    db = next(session_source)
    try:
        protected = db.query(TeamMember).filter_by(display_name="Protected Member").one()
        protected_id = str(protected.id)
    finally:
        session_source.close()

    outsider = setup_project("team-outsider-release@example.com")
    response = outsider.post(
        "/team",
        data={"csrf": csrf(outsider, "/team"), "member_id": protected_id, "display_name": "Outsider Copy", "role": "QA", "capacity_hours_per_day": "4", "working_days": ["Tue"], "active": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Protected Member" in owner.get("/team").text
    assert "Outsider Copy" not in owner.get("/team").text


def test_ai_routes_use_deterministic_fallback_without_credentials():
    client = setup_project("no-ai-credit@example.com")
    response = client.post(
        "/aria",
        data={"csrf": csrf(client, "/aria"), "question": "What is the sprint health?"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/aria")
    assert "There is no active sprint" in page.text
