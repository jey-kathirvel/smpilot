import hashlib
import secrets

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def validate_password(password: str) -> list[str]:
    errors: list[str] = []
    if len(password) < 12:
        errors.append("Password must be at least 12 characters.")
    if not any(character.isalpha() for character in password):
        errors.append("Password must contain a letter.")
    if not any(character.isdigit() for character in password):
        errors.append("Password must contain a number.")
    return errors


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def new_reset_token() -> str:
    return secrets.token_urlsafe(48)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
