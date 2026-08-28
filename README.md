# SMPilot AI

**SMPilot AI** is an AI-driven Scrum execution platform designed to automate the operational responsibilities of a Scrum Master while keeping business and people decisions under human control.

## AI Scrum Master

Meet **Aria** — the autonomous AI Scrum Master inside SMPilot.

Aria helps teams:
- prepare and facilitate sprint planning
- analyze backlog readiness
- collect and summarize daily stand-ups
- detect blockers, dependencies, delivery risks, and stale work
- monitor sprint health and completion probability
- recommend focused meetings only when needed
- track follow-ups and impediments
- facilitate sprint reviews and retrospectives
- generate actionable sprint insights and reports

## Product principles

- AI-first, not dashboard-first
- simplified workflow instead of Jira-level complexity
- mobile responsive and installable as a PWA
- ocean-blue visual system with colorful status and insight elements
- transparent AI recommendations with human approval for consequential actions
- secure multi-user and multi-team data isolation

## Target deployment

- Production: `https://smpilot.ads-ai.in`
- Repository: `jey-kathirvel/smpilot`

## Planned stack

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- Jinja2 / modern vanilla JavaScript frontend
- OpenAI integration for Aria
- PWA manifest + service worker
- Uvicorn behind Apache reverse proxy on Hostinger VPS

## V1 workflow

`Create account → Create team/project → Build backlog → AI sprint planning → Start sprint → Daily updates → Aria monitoring & interventions → Sprint review → AI retrospective → Next sprint`

## Status

Initial product foundation and Codex implementation backlog are being prepared.
