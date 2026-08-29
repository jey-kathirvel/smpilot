"""Idempotently seed a realistic SMPilot V1 demo project.

Usage: set DEMO_OWNER_EMAIL and DEMO_OWNER_PASSWORD, then run
`python scripts/seed_demo.py`. No credentials are printed.
"""
from __future__ import annotations

import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.security import hash_password, validate_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AriaAction,
    DailyStandup,
    Project,
    Sprint,
    SprintItem,
    TeamMember,
    User,
    Workspace,
    WorkspaceMember,
    WorkItem,
    WorkItemDependency,
)

PROJECT_NAME = "Payment Platform Modernization"
PROJECT_KEY = "PAYMOD"


def get_or_create(db: Session, model, defaults: dict | None = None, **identity):
    value = db.scalar(select(model).filter_by(**identity))
    if value:
        return value
    value = model(**identity, **(defaults or {}))
    db.add(value)
    db.flush()
    return value


def seed_demo(db: Session, owner_email: str, owner_password: str) -> Project:
    owner_email = owner_email.strip().casefold()
    owner = db.scalar(select(User).where(User.email == owner_email))
    if not owner:
        errors = validate_password(owner_password)
        if errors:
            raise ValueError(" ".join(errors))
        owner = User(full_name="Priya Raman", email=owner_email, password_hash=hash_password(owner_password), organization_name="Northstar Payments")
        db.add(owner); db.flush()

    workspace = get_or_create(db, Workspace, {"name": "Northstar Payments Demo", "timezone": "Asia/Kolkata"}, owner_user_id=owner.id)
    get_or_create(db, WorkspaceMember, {"role": "Admin"}, workspace_id=workspace.id, user_id=owner.id)
    project = get_or_create(db, Project, {"name": PROJECT_NAME, "description": "Modernize authorization, settlement, reconciliation, and observability.", "status": "Active"}, workspace_id=workspace.id, project_key=PROJECT_KEY)

    people = [
        ("Priya Raman", "Product Owner", owner.id, 6.0),
        ("Arjun Mehta", "Developer", None, 6.0),
        ("Meera Shah", "Developer", None, 6.0),
        ("Nikhil Rao", "Developer", None, 5.5),
        ("Sara Thomas", "QA", None, 6.0),
    ]
    members = {}
    for name, role, user_id, capacity in people:
        member = get_or_create(db, TeamMember, {"workspace_id": workspace.id, "role": role, "user_id": user_id, "capacity_hours_per_day": capacity, "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri"], "active": True}, project_id=project.id, display_name=name)
        members[name] = member

    item_specs = [
        ("Epic", "Modernize payment authorization", "Critical", None, "In Progress", None),
        ("Story", "Introduce idempotent authorization API", "Critical", 8, "Done", "Arjun Mehta"),
        ("Story", "Add gateway timeout recovery", "High", 5, "Done", "Meera Shah"),
        ("Story", "Route traffic through the new risk adapter", "High", 8, "In Progress", "Nikhil Rao"),
        ("Bug", "Resolve duplicate webhook delivery", "Critical", 5, "Blocked", "Arjun Mehta"),
        ("Story", "Automate settlement reconciliation", "High", 8, "Review", "Sara Thomas"),
        ("Task", "Publish payment latency dashboards", "Medium", 3, "Ready", "Meera Shah"),
        ("Story", "Add partial refund workflow", "Medium", 5, "Backlog", "Nikhil Rao"),
        ("Story", "Expose dispute evidence timeline", "Medium", 5, "Backlog", "Sara Thomas"),
        ("Task", "Complete PCI threat-model review", "High", 3, "Backlog", "Arjun Mehta"),
    ]
    items = []
    epic = None
    for index, (kind, title, priority, points, status, assignee) in enumerate(item_specs, 1):
        item = get_or_create(db, WorkItem, {"type": kind, "description": f"Demo scope for {title.lower()}.", "acceptance_criteria": "Observable acceptance evidence is available and reviewed by the team.", "priority": priority, "story_points": points, "status": status, "assignee_id": members[assignee].id if assignee else None, "reporter_id": owner.id, "epic_id": epic.id if epic and kind != "Epic" else None, "archived": False}, project_id=project.id, item_key=f"{PROJECT_KEY}-{index}", title=title)
        items.append(item)
        if kind == "Epic": epic = item

    get_or_create(db, WorkItemDependency, {"relation_type": "Blocked By"}, source_item_id=items[4].id, target_item_id=items[2].id)
    today = date.today()
    completed_specs = [("Sprint 21", 34, 29, 42), ("Sprint 22", 31, 31, 28), ("Sprint 23", 36, 32, 14)]
    for offset, (name, planned, delivered, days_ago) in enumerate(completed_specs):
        end = today - timedelta(days=days_ago)
        sprint = get_or_create(db, Sprint, {"goal": f"Incrementally de-risk payment modernization milestone {21 + offset}.", "start_date": end - timedelta(days=13), "end_date": end, "status": "Completed", "planned_points": planned, "completed_points": delivered}, project_id=project.id, name=name)
        for item in items[1:4]:
            membership = get_or_create(db, SprintItem, {"final_status": "Done"}, sprint_id=sprint.id, work_item_id=item.id)
            membership.final_status = "Done"

    active = get_or_create(db, Sprint, {"goal": "Stabilize authorization recovery and prove automated settlement reconciliation.", "start_date": today - timedelta(days=6), "end_date": today + timedelta(days=7), "status": "Active", "planned_points": 29, "completed_points": 13}, project_id=project.id, name="Sprint 24")
    for item in items[1:7]:
        get_or_create(db, SprintItem, {}, sprint_id=active.id, work_item_id=item.id)
    items[4].updated_at = datetime.now(UTC) - timedelta(days=2, hours=6)

    get_or_create(db, DailyStandup, {"sprint_id": active.id, "yesterday": "Validated authorization retry behavior and reviewed settlement mismatches.", "today": "Clarify the webhook ownership decision and protect the sprint goal.", "blockers": "Vendor sandbox intermittently duplicates webhook delivery.", "confidence": 0.65, "status": "Submitted"}, project_id=project.id, user_id=owner.id, update_date=today)
    get_or_create(db, AriaAction, {"sprint_id": active.id, "action_type": "Escalate Dependency", "description": "Confirm vendor webhook ownership and recovery SLA before the blocked story ages further.", "status": "Suggested", "consequential": True, "created_by_user_id": owner.id, "expires_at": datetime.now(UTC) + timedelta(days=2)}, project_id=project.id, title="Resolve duplicate webhook dependency")
    get_or_create(db, AriaAction, {"sprint_id": active.id, "action_type": "Facilitate Focused Discussion", "description": "Run a focused 15-minute discussion on settlement mismatch evidence.", "status": "Approved", "consequential": False, "created_by_user_id": owner.id, "approved_by_user_id": owner.id, "approved_at": datetime.now(UTC)}, project_id=project.id, title="Review settlement reconciliation evidence")
    db.commit()
    return project


def main() -> int:
    email = os.getenv("DEMO_OWNER_EMAIL", "").strip()
    password = os.getenv("DEMO_OWNER_PASSWORD", "")
    if not email or not password:
        print("Set DEMO_OWNER_EMAIL and DEMO_OWNER_PASSWORD before seeding.", file=sys.stderr)
        return 2
    with SessionLocal() as db:
        project = seed_demo(db, email, password)
        print(f"Demo project ready: {project.name} ({project.project_key})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
