import re
from datetime import date, timedelta

from app.ai.schemas import SprintPlanRecommendation
from app.config import Settings
from tests import test_auth as _test_auth  # noqa: F401 - installs the test DB override
from tests.test_backlog import csrf, setup_project


def create_planning_scenario(email: str):
    client = setup_project(email)
    item_response = client.post("/backlog", data={"csrf": csrf(client, "/backlog"), "type": "Story", "title": "Ship payment", "description": "", "acceptance_criteria": "Payment succeeds", "priority": "Critical", "story_points": "5", "status": "Ready", "assignee_id": ""}, follow_redirects=False)
    item_id = item_response.headers["location"].rsplit("/", 1)[-1]
    today = date.today()
    client.post("/sprint", data={"csrf": csrf(client, "/sprint"), "name": "Sprint Plan", "goal": "Ship a safe increment", "start_date": today.isoformat(), "end_date": (today + timedelta(days=13)).isoformat()})
    page = client.get("/sprint").text
    sprint_id = re.search(r'action="/sprint/([^/]+)/items"', page).group(1)
    return client, item_id, sprint_id


def test_aria_plan_requires_human_acceptance_before_scope_change(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.aria_planner.get_settings", lambda: Settings(openai_api_key="", _env_file=None))
    client, item_id, sprint_id = create_planning_scenario("planner@example.com")
    response = client.post(f"/sprint/{sprint_id}/aria-plan", data={"csrf": csrf(client, "/sprint/planning")}, follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/sprint/planning").text
    assert "Planned points</span><strong>0" in client.get("/sprint").text
    assert "PAY-1" in page and "Accept recommendation" in page
    plan_id = re.search(r'action="/sprint/plans/([^/]+)/decision"', page).group(1)
    response = client.post(f"/sprint/plans/{plan_id}/decision", data={"csrf": csrf(client, "/sprint/planning"), "decision": "Accepted"}, follow_redirects=False)
    assert response.status_code == 303
    sprint_page = client.get("/sprint").text
    assert "Planned points</span><strong>5" in sprint_page


def test_sprint_plan_schema_defaults_to_human_approval() -> None:
    plan = SprintPlanRecommendation(
        sprint_goal="Ship safely",
        recommended_story_ids=[],
        recommended_story_keys=[],
        expected_story_points=0,
        capacity_utilization=0,
        rationale="No ready work is available.",
        confidence=1,
    )
    assert plan.requires_human_approval is True
