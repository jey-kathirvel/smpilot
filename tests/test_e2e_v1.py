import re
from datetime import date, timedelta

from tests import test_auth as _test_auth  # noqa: F401
from tests.test_backlog import csrf, setup_project


def test_complete_aria_operating_loop():
    client = setup_project("v1-e2e@example.com")
    assert client.get("/settings/workspace").status_code == 200
    assert client.get("/settings/projects").status_code == 200
    client.post("/team", data={"csrf": csrf(client, "/team"), "display_name": "Delivery Lead", "role": "Product Owner", "capacity_hours_per_day": "6", "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri"], "active": "true"})
    assert "Delivery Lead" in client.get("/team").text

    item_response = client.post(
        "/backlog",
        data={"csrf": csrf(client, "/backlog"), "type": "Story", "title": "Recover payment authorization", "description": "Retry safely", "acceptance_criteria": "A timed-out request is idempotently recovered", "priority": "Critical", "story_points": "5", "status": "Ready", "assignee_id": ""},
        follow_redirects=False,
    )
    item_id = item_response.headers["location"].rsplit("/", 1)[-1]
    today = date.today()
    client.post("/sprint", data={"csrf": csrf(client, "/sprint"), "name": "V1 UAT Sprint", "goal": "Prove the autonomous Aria loop", "start_date": today.isoformat(), "end_date": (today + timedelta(days=3)).isoformat()})
    sprint_page = client.get("/sprint").text
    sprint_id = re.search(r'action="/sprint/([^/]+)/items"', sprint_page).group(1)

    planned = client.post(f"/sprint/{sprint_id}/aria-plan", data={"csrf": csrf(client, "/sprint/planning")}, follow_redirects=False)
    assert planned.status_code == 303
    plan_page = client.get("/sprint/planning").text
    plan_id = re.search(r'action="/sprint/plans/([^/]+)/decision"', plan_page).group(1)
    assert "Accept recommendation" in plan_page
    assert client.post(f"/sprint/plans/{plan_id}/decision", data={"csrf": csrf(client, "/sprint/planning"), "decision": "Accepted"}, follow_redirects=False).status_code == 303
    assert client.post(f"/sprint/{sprint_id}/start", data={"csrf": csrf(client, "/sprint")}, follow_redirects=False).status_code == 303

    assert client.post("/standup", data={"csrf": csrf(client, "/standup"), "yesterday": "Prepared retry tests", "today": "Resolve the authorization blocker", "blockers": "Gateway sandbox is unstable", "confidence": "0.6"}, follow_redirects=False).status_code == 303
    assert client.post("/standup/summary", data={"csrf": csrf(client, "/standup")}, follow_redirects=False).status_code == 303
    assert "Aria Morning Brief" in client.get("/today").text

    assert client.post(f"/sprint/{sprint_id}/items/{item_id}/status", data={"csrf": csrf(client, "/sprint"), "status": "Blocked"}, follow_redirects=False).status_code == 303
    sprint_view = client.get("/sprint").text
    assert "Deterministic health" in sprint_view and "Aria risk intelligence" in sprint_view
    assert client.post("/aria/actions/generate", data={"csrf": csrf(client, "/aria/actions")}, follow_redirects=False).status_code == 303
    assert "Suggested" in client.get("/aria/actions").text
    assert client.post("/aria", data={"csrf": csrf(client, "/aria"), "question": "What is blocking this sprint?"}, follow_redirects=False).status_code == 303
    assert "blocked item" in client.get("/aria").text

    assert client.post(f"/sprint/{sprint_id}/items/{item_id}/status", data={"csrf": csrf(client, "/sprint"), "status": "Done"}, follow_redirects=False).status_code == 303
    assert client.post(f"/sprint/{sprint_id}/complete", data={"csrf": csrf(client, "/sprint"), "unfinished_action": "backlog"}, follow_redirects=False).status_code == 303
    assert "Completed stories" in client.get(f"/sprints/{sprint_id}/review").text
    retro_path = f"/sprints/{sprint_id}/retro"
    assert client.post(retro_path, data={"csrf": csrf(client, retro_path), "category": "Went Well", "content": "Aria kept the sprint focused"}, follow_redirects=False).status_code == 303
    assert client.post(f"{retro_path}/actions", data={"csrf": csrf(client, retro_path), "title": "Keep blocker reviews", "description": "Review aging blockers daily", "owner": "Team", "due_date": ""}, follow_redirects=False).status_code == 303
    assert "Keep blocker reviews" in client.get(retro_path).text
    insights = client.get("/insights")
    assert insights.status_code == 200 and "V1 UAT Sprint" in insights.text
