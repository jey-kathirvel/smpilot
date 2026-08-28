import re
from datetime import date, timedelta
from tests.test_backlog import csrf, setup_project


def test_health_is_deterministic_and_complete() -> None:
    client = setup_project("health-owner@example.com"); today = date.today()
    client.post("/sprint", data={"csrf": csrf(client, "/sprint"), "name": "Health Sprint", "goal": "Be predictable", "start_date": today.isoformat(), "end_date": (today + timedelta(days=9)).isoformat()})
    sprint_id = re.search(r'action="/sprint/([^/]+)/items"', client.get("/sprint").text).group(1)
    client.post(f"/sprint/{sprint_id}/start", data={"csrf": csrf(client, "/sprint")})
    first = client.get("/sprint").text; second = client.get("/sprint").text
    first_result = re.search(r"Sprint health</span><strong>([^<]+)</strong><span class=\"muted\">Score (\d+)", first).groups()
    second_result = re.search(r"Sprint health</span><strong>([^<]+)</strong><span class=\"muted\">Score (\d+)", second).groups()
    assert first_result == second_result and first_result[0].strip() in {"ON TRACK", "AT RISK", "CRITICAL"}
    assert "Deterministic health" in first and "Why" in first
