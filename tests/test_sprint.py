import re
from datetime import date, timedelta

from tests.test_backlog import csrf, setup_project


def test_complete_sprint_lifecycle() -> None:
    client = setup_project("sprint-owner@example.com")
    item_response = client.post("/backlog", data={"csrf": csrf(client, "/backlog"), "type": "Story", "title": "Checkout", "description": "", "acceptance_criteria": "Checkout succeeds", "priority": "High", "story_points": "5", "status": "Ready", "assignee_id": ""}, follow_redirects=False)
    item_id = item_response.headers["location"].rsplit("/", 1)[-1]
    today = date.today()
    response = client.post("/sprint", data={"csrf": csrf(client, "/sprint"), "name": "Sprint 01", "goal": "Ship checkout", "start_date": today.isoformat(), "end_date": (today + timedelta(days=13)).isoformat()}, follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/sprint").text
    sprint_id = re.search(r'action="/sprint/([^/]+)/items"', page).group(1)
    response = client.post(f"/sprint/{sprint_id}/items", data={"csrf": csrf(client, "/sprint"), "item_ids": item_id}, follow_redirects=False)
    assert response.status_code == 303
    assert "5" in client.get("/sprint").text
    assert client.post(f"/sprint/{sprint_id}/start", data={"csrf": csrf(client, "/sprint")}, follow_redirects=False).status_code == 303
    board = client.get("/sprint").text
    assert "Checkout" in board and "Ready" in board
    response = client.post(f"/sprint/{sprint_id}/items/{item_id}/status", data={"csrf": csrf(client, "/sprint"), "status": "Done"}, follow_redirects=False)
    assert response.status_code == 303
    assert client.post(f"/sprint/{sprint_id}/complete", data={"csrf": csrf(client, "/sprint"), "unfinished_action": "backlog"}, follow_redirects=False).status_code == 303
    assert "Create sprint" in client.get("/sprint").text
