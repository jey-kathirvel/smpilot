from app.services.history import sprint_history
from tests.test_auth import TestingSession
import uuid
def test_empty_history_is_team_focused_and_deterministic():
    with TestingSession() as db:
        result=sprint_history(db,uuid.UUID("00000000-0000-0000-0000-000000000000"))
    assert result["sprints"]==[] and "Complete at least two sprints" in result["trends"][0]
    assert "member" not in str(result).lower() and "employee" not in str(result).lower()
