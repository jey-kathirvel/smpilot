from tests import test_auth as _test_auth  # noqa:F401
from tests.test_backlog import setup_project
def test_daily_scrum_has_meeting_recommendation():
    client=setup_project("meeting@example.com"); page=client.get("/standup/meeting").text
    assert "Aria recommendation" in page and ("No Scrum Meeting Needed" in page or "Focused Sync Recommended" in page)
    assert "does not book calendars" in page
