from app.services.persona import ARIA_IDENTITY, ARIA_STATES, aria_state
from tests.test_backlog import setup_project


def test_aria_identity_and_supported_states():
    assert ARIA_IDENTITY == {"name": "Aria", "role": "AI Scrum Master", "product": "SMPilot AI"}
    assert ARIA_STATES == ("On Track", "Analyzing", "Risk Detected", "Blocked", "Planning", "Sprint Complete")
    assert aria_state(health="CRITICAL") == "Blocked"
    assert aria_state(health="AT_RISK") == "Risk Detected"
    assert aria_state(activity="Planning") == "Planning"


def test_aria_identity_is_visible_in_authenticated_experience():
    client = setup_project("persona@example.com")
    page = client.get("/today")
    assert page.status_code == 200
    assert "Aria" in page.text
    assert "AI Scrum Master" in page.text
    assert 'data-state="On Track"' in page.text
