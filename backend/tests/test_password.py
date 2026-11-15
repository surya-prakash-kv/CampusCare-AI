
from argon2 import PasswordHasher

from app.services.password import (
    hash_password,
    verify_password,
    password_needs_rehash,
)


def test_hash_password_creates_verifiable_hash():
    password = "StrongTestPassword123!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)


def test_verify_password_rejects_wrong_password():
    password_hash = hash_password("StrongTestPassword123!")

    assert not verify_password("WrongPassword123!", password_hash)


def test_verify_password_rejects_invalid_hash():
    assert not verify_password("password", "invalid-hash")


def test_password_needs_rehash_returns_false_for_current_hash():
    password_hash = hash_password("StrongTestPassword123!")

    assert password_needs_rehash(password_hash) is False


def test_password_needs_rehash_detects_outdated_parameters():
    old_hasher = PasswordHasher(
        time_cost=1,
        memory_cost=1024,
        parallelism=1,
    )
    old_hash = old_hasher.hash("StrongTestPassword123!")

    assert password_needs_rehash(old_hash) is True
