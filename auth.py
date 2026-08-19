import hashlib
import os
import re
import database


def _hash_password(password: str, salt: bytes | None = None) :
    if salt is None:
        salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 200_000
    )
    return hash_bytes.hex(), salt.hex()


def _is_valid_username(username: str):
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,20}", username))


def _is_valid_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return False, "Password must contain both letters and numbers."
    return True, ""


def signup(username: str, password: str) :
    username = username.strip()

    if not _is_valid_username(username):
        return False, "Username must be 3-20 characters: letters, numbers, underscores only."

    valid, reason = _is_valid_password(password)
    if not valid:
        return False, reason

    if database.username_exists(username):
        return False, "That username is already taken."

    password_hash, salt = _hash_password(password)
    database.create_user(username, password_hash, salt)
    return True, f"Account created for {username}."


def login(username: str, password: str) :
    username = username.strip()
    user = database.get_user(username)

    if user is None:
        return False, "No account found with that username."

    salt = bytes.fromhex(user["salt"])
    expected_hash, _ = _hash_password(password, salt)

    if expected_hash != user["password_hash"]:
        return False, "Incorrect password."

    database.update_last_login(username)
    return True, f"Welcome back, {username}."
