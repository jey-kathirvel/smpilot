# SMPilot Hostinger Deployment

Target: `https://smpilot.ads-ai.in`, application `/opt/smpilot`, service `smpilot.service`, loopback port `8130`.

## Prerequisites

Confirm DNS points to the VPS and verify port 8130 is unused before installation. Create a dedicated `smpilot` system account and PostgreSQL role/database. Do not reuse another application's user, port, vhost, database, or environment file.

## Application

Clone the trusted repository into `/opt/smpilot`, owned by `smpilot`. Create `/opt/smpilot/.venv`, install `requirements.txt`, and create `/opt/smpilot/.env` with mode `0600`:

```text
APP_ENV=production
APP_DEBUG=false
APP_BASE_URL=https://smpilot.ads-ai.in
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1/smpilot
SESSION_SECRET=at-least-32-random-characters
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
```

Generate secrets outside the repository. Never paste credentials into service files, shell history, Git, logs, or smoke-check output.

Run migrations as the service user:

```text
sudo -u smpilot /opt/smpilot/.venv/bin/alembic -c /opt/smpilot/alembic.ini upgrade head
```

## systemd

Copy `deploy/smpilot.service.example` to `/etc/systemd/system/smpilot.service`, review the user, paths, and confirmed free port, then reload systemd, enable, and start only this service. Validate with `systemctl status smpilot.service` and `curl http://127.0.0.1:8130/health`.

## Apache and TLS

Enable `proxy`, `proxy_http`, `headers`, `rewrite`, and `ssl`. Install the reviewed vhost as a distinct Apache site; do not edit unrelated vhosts. Validate with `apachectl configtest` before reloading Apache.

After the HTTP vhost resolves correctly, request and install TLS using Certbot's Apache integration for only `smpilot.ads-ai.in`. Verify automatic renewal with `certbot renew --dry-run` and confirm HTTP redirects to HTTPS.

## Release procedure

1. Fetch and fast-forward `/opt/smpilot` to the reviewed `origin/main` revision.
2. Install locked project requirements inside `.venv`.
3. Run `alembic upgrade head`.
4. Restart only `smpilot.service`.
5. Run `scripts/smoke-production.sh https://smpilot.ads-ai.in`.
6. Confirm the deployed Git revision matches the approved GitHub commit.

Back up PostgreSQL before migrations. Rollback means restoring the tested database backup and previous reviewed Git revision; never use destructive repository scripts against production.
