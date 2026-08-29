from pathlib import Path


def test_smoke_script_checks_required_routes_without_bodies_or_secrets():
    script = Path("scripts/smoke-production.sh").read_text()
    for route in ("/login", "/signup", "/health", "/manifest.json", "/service-worker.js"):
        assert route in script
    assert "systemctl is-active smpilot.service" in script
    assert "git -C /opt/smpilot rev-parse HEAD" in script
    assert "--output /dev/null" in script
    assert "API_KEY" not in script and "SESSION_SECRET" not in script
