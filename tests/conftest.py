import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def disable_external_ai_by_default(monkeypatch):
    """The test suite must never spend external model credits."""
    settings = get_settings()
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
