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

## Local development

Requirements: Python 3.12+ and PostgreSQL.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Create a PostgreSQL database and update `DATABASE_URL` in `.env`. Replace
`SESSION_SECRET` with a long random value. Never commit `.env`.

Initialize or update the database and start the application:

```bash
alembic upgrade head
python run.py
```

Open `http://localhost:8000`. The health check is available at `/health`.

Run the test suite with:

```bash
pytest
```

## Configuration

Runtime settings are loaded from environment variables. See `.env.example` for
application, PostgreSQL, session, OpenAI, and SMTP settings. OpenAI and SMTP are
optional for the initial foundation.

Authentication uses signed, HttpOnly, SameSite session cookies and Argon2
password hashing. In production, `SESSION_SECRET` is mandatory and cookies are
marked Secure. Configure the SMTP variables to deliver password-reset links;
reset requests return the same response whether or not an account exists.

## Project structure

- `app/`: FastAPI application, routes, templates, static assets, and services
- `migrations/`: Alembic migration environment and revisions
- `scripts/`: maintenance and operational scripts
- `tests/`: automated tests

## Status

The production-oriented FastAPI foundation is in place. Authentication and the
remaining Scrum workflow are implemented in subsequent roadmap tasks.
