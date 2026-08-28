# Automated Test Suite

Run the release suite with:

```text
python -m pytest -q
```

External AI credentials are disabled by an autouse test fixture. Provider success and failure behavior uses local fake clients, while route tests exercise deterministic fallbacks; the suite consumes no OpenAI or OpenRouter credits.

Coverage includes startup and health, complete authentication and reset flows, user/workspace/project/team isolation, backlog CRUD, sprint lifecycle and health, stand-ups and blockers, structured AI parsing and provider failure, Aria Actions and approval gates, retrospectives, notifications, PWA assets, mobile layout contracts, and production security controls.
