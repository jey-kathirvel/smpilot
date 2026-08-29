from pathlib import Path

from tests.test_backlog import setup_project


def test_glassy_ocean_design_tokens_and_navigation_state():
    css = Path("app/static/css/app.css").read_text()
    assert "--surface:rgba(255,255,255,.76)" in css
    assert "backdrop-filter:blur(24px)" in css
    assert "--blue:#087fb9" in css
    assert "background:linear-gradient(145deg,#f8fdff" in css
    client = setup_project("design-system@example.com")
    page = client.get("/backlog")
    assert page.status_code == 200
    assert 'class="active" href="/backlog"' in page.text


def test_immersive_ocean_workspace_theme_asset():
    css = Path("app/static/css/app.css").read_text()
    background = Path("app/static/images/ocean-workspace-bg.png")
    assert background.exists()
    assert background.stat().st_size > 100_000
    assert 'url("/static/images/ocean-workspace-bg.png")' in css
    assert "backdrop-filter:blur(16px)" in css
