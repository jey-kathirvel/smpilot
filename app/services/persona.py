ARIA_IDENTITY = {"name": "Aria", "role": "AI Scrum Master", "product": "SMPilot AI"}

ARIA_STATES = (
    "On Track",
    "Analyzing",
    "Risk Detected",
    "Blocked",
    "Planning",
    "Sprint Complete",
)


def aria_state(*, health: str | None = None, activity: str | None = None) -> str:
    """Return a stable presentation state without inventing delivery facts."""
    if activity in ARIA_STATES:
        return activity
    if health == "CRITICAL":
        return "Blocked"
    if health == "AT_RISK":
        return "Risk Detected"
    return "On Track"
