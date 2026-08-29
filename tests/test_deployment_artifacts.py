from pathlib import Path


def test_production_examples_are_scoped_and_secret_free():
    service = Path("deploy/smpilot.service.example").read_text()
    apache = Path("deploy/apache-smpilot.conf.example").read_text()
    guide = Path("deploy/deployment.md").read_text()
    assert "User=smpilot" in service
    assert "127.0.0.1 --port 8130" in service
    assert "EnvironmentFile=/opt/smpilot/.env" in service
    assert "Restart=on-failure" in service
    assert "smpilot.ads-ai.in" in apache
    assert "http://127.0.0.1:8130/" in apache
    assert "Certbot" in guide and "apachectl configtest" in guide
    assert "OPENAI_API_KEY=" in guide and "OPENAI_MODEL=" in guide
