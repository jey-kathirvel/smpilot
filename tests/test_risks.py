import re
from datetime import date, timedelta
from tests.test_backlog import csrf, setup_project


def test_unestimated_work_produces_confidence_scored_risk() -> None:
    client = setup_project("risk-owner@example.com")
    response = client.post("/backlog", data={"csrf": csrf(client, "/backlog"), "type": "Story", "title": "Unknown effort", "description": "", "acceptance_criteria": "", "priority": "High", "story_points": "", "status": "Ready", "assignee_id": ""}, follow_redirects=False)
    item_id = response.headers["location"].rsplit("/", 1)[-1]; today = date.today()
    client.post("/sprint", data={"csrf": csrf(client, "/sprint"), "name": "Risk Sprint", "goal": "Surface risk", "start_date": today.isoformat(), "end_date": (today + timedelta(days=2)).isoformat()})
    sprint_id = re.search(r'action="/sprint/([^/]+)/items"', client.get("/sprint").text).group(1)
    client.post(f"/sprint/{sprint_id}/items", data={"csrf": csrf(client, "/sprint"), "item_ids": item_id})
    page = client.get("/sprint").text
    assert "PAY-1 is unestimated" in page
    assert "may reduce forecast confidence" in page and "Confidence 90%" in page
