from typing import Any


def sanitize_context(value: Any) -> Any:
    """Bound untrusted text while preserving facts for model context."""
    if isinstance(value, str):
        return "".join(character for character in value[:4000] if character in "\n\t" or ord(character) >= 32)
    if isinstance(value, dict):
        return {str(key)[:100]: sanitize_context(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_context(item) for item in value[:250]]
    return value
