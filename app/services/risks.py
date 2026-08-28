from datetime import UTC, datetime
from collections import Counter
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.backlog import WorkItem, WorkItemDependency
from app.models.organization import TeamMember
from app.models.sprint import Sprint, SprintItem
from app.services.health import sprint_health


def sprint_risks(db: Session, sprint: Sprint) -> list[dict]:
    items = db.scalars(select(WorkItem).join(SprintItem, SprintItem.work_item_id == WorkItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None))).all()
    members = db.scalars(select(TeamMember).where(TeamMember.project_id == sprint.project_id, TeamMember.active.is_(True))).all(); health = sprint_health(db, sprint); risks = []; now = datetime.now(UTC)
    def add(level, title, detail, confidence, reasons, item=None): risks.append({"level": level, "title": title, "detail": detail, "confidence": confidence, "reasons": reasons, "item_id": str(item.id) if item else None})
    for item in items:
        updated = item.updated_at if item.updated_at.tzinfo else item.updated_at.replace(tzinfo=UTC); age_hours = max(0, (now - updated).total_seconds() / 3600)
        if item.status == "Blocked": add("HIGH" if age_hours >= 24 else "MEDIUM", f"{item.item_key} is blocked", f"{item.item_key} may miss its expected delivery window.", min(.95, .65 + age_hours / 240), [f"Blocked for {age_hours:.0f} hours", f"{item.story_points or 0} points remain"], item)
        if item.status in {"In Progress", "Review"} and age_hours >= 48: add("MEDIUM", f"{item.item_key} is stale", f"{item.item_key} may need coordination.", .78, [f"No activity for {age_hours / 24:.1f} days"], item)
        if item.story_points is None: add("MEDIUM", f"{item.item_key} is unestimated", "Unestimated sprint work may reduce forecast confidence.", .9, ["No story-point estimate"], item)
        if not item.acceptance_criteria and item.type in {"Story", "Bug"}: add("MEDIUM", f"{item.item_key} lacks acceptance criteria", "The item may require refinement before completion.", .88, ["Acceptance criteria are missing"], item)
    remaining = health["remaining_points"]
    if health["available_days"] <= 3 and remaining > 0: add("HIGH", "Sprint spillover risk", "Some sprint work may spill into the next sprint.", min(.92, .6 + remaining / max(10, sprint.planned_points or 10) * .3), [f"{remaining} points remain", f"Only {health['available_days']} sprint days remain"])
    assigned = Counter(item.assignee_id for item in items if item.assignee_id and item.status not in {"Done", "Backlog"})
    for member in members:
        if assigned[member.id] > 2: add("MEDIUM", f"{member.display_name} may be overloaded", "Parallel work may reduce delivery flow.", .75, [f"{assigned[member.id]} active items assigned"])
    qa = [member for member in members if member.role == "QA"]; review_count = sum(1 for item in items if item.status == "Review")
    if review_count > max(1, len(qa) * 2): add("HIGH", "QA capacity may be insufficient", "Review demand may exceed available QA capacity.", .8, [f"{review_count} items await review", f"{len(qa)} active QA member(s)"])
    links = db.scalars(select(WorkItemDependency).where(WorkItemDependency.source_item_id.in_([item.id for item in items]))).all() if items else []
    targets = Counter(link.target_item_id for link in links)
    if targets and max(targets.values()) >= 2: add("HIGH", "Dependency bottleneck detected", "Multiple sprint items may depend on the same delivery path.", .82, [f"{max(targets.values())} dependencies converge on one item"])
    if health["scope_added_points"] > 0: add("MEDIUM", "Sprint scope has increased", "Added scope may put the sprint goal at risk.", .85, [f"{health['scope_added_points']} points added after sprint start"])
    wip = sum(1 for item in items if item.status in {"In Progress", "Blocked", "Review"})
    if wip > max(3, len(members) * 2): add("MEDIUM", "Work in progress is excessive", "High parallel work may slow completion.", .8, [f"{wip} items are currently in progress"])
    return sorted(risks, key=lambda risk: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[risk["level"]], -risk["confidence"]))
