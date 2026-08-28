from tests import test_auth as _test_auth  # noqa: F401
from tests.test_backlog import csrf, setup_project


def test_today_has_useful_empty_state() -> None:
    client = setup_project("today-owner@example.com")
    page = client.get("/today")
    assert page.status_code == 200 and "Set up your operating view" in page.text


def test_today_shows_active_sprint_metrics() -> None:
    import re
    from datetime import date, timedelta
    client = setup_project("today-sprint@example.com"); today = date.today()
    client.post("/sprint", data={"csrf": csrf(client, "/sprint"), "name": "Sprint 10", "goal": "Operate daily", "start_date": today.isoformat(), "end_date": (today + timedelta(days=9)).isoformat()})
    sprint_id = re.search(r'action="/sprint/([^/]+)/items"', client.get("/sprint").text).group(1)
    client.post(f"/sprint/{sprint_id}/start", data={"csrf": csrf(client, "/sprint")})
    page = client.get("/today").text
    assert "Aria reviewed Sprint 10" in page and "Sprint day" in page and "Likely to complete" in page
