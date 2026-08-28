import re
import uuid
from datetime import date, timedelta
from sqlalchemy import select
from app.models.sprint import Sprint
from app.services.health import sprint_health
from tests.test_auth import TestingSession
from tests.test_backlog import csrf, setup_project


def test_health_is_deterministic_and_complete() -> None:
    client = setup_project("health-owner@example.com"); today = date.today()
    client.post("/sprint", data={"csrf": csrf(client, "/sprint"), "name": "Health Sprint", "goal": "Be predictable", "start_date": today.isoformat(), "end_date": (today + timedelta(days=9)).isoformat()})
    sprint_id = re.search(r'action="/sprint/([^/]+)/items"', client.get("/sprint").text).group(1)
    client.post(f"/sprint/{sprint_id}/start", data={"csrf": csrf(client, "/sprint")})
    with TestingSession() as db:
        sprint = db.scalar(select(Sprint).where(Sprint.id == uuid.UUID(sprint_id)))
        first = sprint_health(db, sprint, today); second = sprint_health(db, sprint, today)
    assert first == second and first["status"] in {"ON_TRACK", "AT_RISK", "CRITICAL"}
    expected = {"elapsed_sprint_percent", "completion_percent", "completed_story_points", "remaining_points", "blocked_points", "blocked_item_count", "average_blocker_age_hours", "stale_work_count", "scope_added_points", "scope_removed_points", "available_days", "team_capacity_points", "historical_velocity", "missing_updates", "reasons", "score"}
    assert expected <= first.keys()
