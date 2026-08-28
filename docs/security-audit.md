# SMPilot Security Audit

Completed for Task 23 on 2026-08-29. The review covered application routes, ORM queries, templates, sessions, password reset, AI context construction, and production configuration.

## Findings and controls

| Area | Result and control |
|---|---|
| Object/workspace/project authorization | Scoped ORM queries resolve the authenticated user's workspace or project before reading or mutating records. Nested sprint, backlog, plan, action, retro, team, insight, and notification objects are constrained to that authorized parent. Cross-project tests cover representative IDOR attempts. |
| CSRF | Every state-changing browser route validates a session-bound token with constant-time comparison. |
| Sessions and cookies | Signed sessions enforce user `session_version`, inactivity lifetime, SameSite=Lax, and Secure cookies in production. Production refuses weak session secrets shorter than 32 characters. |
| SQL injection | Queries use SQLAlchemy expressions and bound parameters; user input is not interpolated into SQL. |
| XSS and unsafe HTML | Jinja auto-escaping remains enabled. User data is rendered as text. A restrictive CSP, frame denial, MIME sniffing protection, referrer policy, and permissions policy are applied globally. |
| Password reset | Reset tokens are random, stored only as SHA-256 digests, single-use, expiring, and invalidate existing sessions after password change. Login performs dummy password verification for unknown accounts. |
| Secrets and logs | Secret settings are excluded from representations. AI audit rows store a context hash rather than prompts; application logs do not log request bodies, passwords, reset codes, API keys, or model context. |
| File access | No user-controlled filesystem paths or uploads exist in the V1 application. Static paths are served from the fixed application directory. |
| Request abuse | Request bodies over 1 MiB are rejected. AI-generating routes are rate limited per authenticated user and feature. |
| AI isolation | Context is constructed only after project authorization and every query is project-scoped. No conversation context is shared between users. |
| Prompt injection | The system prompt explicitly labels work-item and stand-up content as untrusted data that cannot override instructions. Context strings and collection sizes are bounded and control characters are removed. External model responses must validate against typed Pydantic schemas; failures use deterministic fallbacks. |

## Residual operational considerations

- The built-in AI limiter is process-local. If production scales to multiple application workers, replace it with a shared Redis-backed limiter.
- Rotate session, SMTP, database, and AI credentials through the VPS environment file and never commit them.
- Keep reverse-proxy request limits, TLS configuration, OS packages, and Python dependencies patched.
- Run dependency and dynamic security scans as part of the release process; this audit does not claim formal penetration-test coverage.
