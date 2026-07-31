import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from types import SimpleNamespace
from uuid import uuid4

import fakeredis
import pytest
from pydantic import ValidationError
from redis.exceptions import RedisError

from app.core import security
from app.core.exceptions import BusinessRuleException
from app.modules.auth import services, token_store
from app.modules.auth.schemas import UserCreate


class AtomicRedisFake:
    def __init__(self, unavailable: bool = False):
        self.sessions = {}
        self.lock = Lock()
        self.unavailable = unavailable

    def eval(self, script, key_count, key, *arguments):
        if self.unavailable:
            raise RedisError("unavailable")

        with self.lock:
            if script == token_store.CREATE_SESSION_SCRIPT:
                if key in self.sessions:
                    return 0
                self.sessions[key] = {
                    "user_id": arguments[0],
                    "current_jti": arguments[1],
                    "state": "active",
                }
                return 1

            if script == token_store.ROTATE_SESSION_SCRIPT:
                session = self.sessions.get(key)
                if not session or session["state"] != "active":
                    return 0
                if (
                    session["user_id"] != arguments[0]
                    or session["current_jti"] != arguments[1]
                ):
                    session["state"] = "revoked"
                    session.pop("current_jti", None)
                    return -1
                session["current_jti"] = arguments[2]
                return 1

            if script == token_store.REVOKE_SESSION_SCRIPT:
                session = self.sessions.get(key)
                if not session:
                    return 0
                session["state"] = "revoked"
                session.pop("current_jti", None)
                return 1

            raise AssertionError("Unexpected Lua script")


@pytest.fixture
def user():
    return SimpleNamespace(
        user_id=uuid4(),
        email="user@example.com",
        role="customer",
    )


@pytest.fixture
def auth_services(monkeypatch, user):
    monkeypatch.setattr(services, "authenticate_user", lambda *args: user)
    monkeypatch.setattr(services, "get_user_by_id", lambda *args, **kwargs: user)
    return user


def test_access_and_refresh_tokens_are_not_interchangeable(user):
    payload = services._token_payload(user)
    session_id = uuid4()
    refresh_jti = uuid4()
    access_token = security.create_access_token(payload)
    refresh_token = security.create_refresh_token(payload, session_id, refresh_jti)

    assert security.decode_token(access_token, "access") is not None
    assert security.decode_token(access_token, "refresh") is None
    assert security.decode_token(refresh_token, "refresh") is not None
    assert security.decode_token(refresh_token, "access") is None


def test_password_hashing_uses_compatible_bcrypt_api():
    password = "StrongPass1"
    hashed_password = security.hash_password(password)

    assert security.verify_password(password, hashed_password)
    assert not security.verify_password("WrongPass1", hashed_password)


def test_passwords_over_bcrypt_byte_limit_are_rejected():
    with pytest.raises(ValidationError):
        UserCreate(
            email="user@example.com",
            name="User",
            password="A1" + ("x" * 71),
        )


def test_refresh_replay_revokes_the_successor(auth_services):
    redis_client = AtomicRedisFake()
    original = services.login_user(None, "user@example.com", "password", redis_client)
    successor = services.refresh_access_token(
        None,
        original["refresh_token"],
        redis_client,
    )

    with pytest.raises(BusinessRuleException) as replay_error:
        services.refresh_access_token(None, original["refresh_token"], redis_client)
    assert replay_error.value.status_code == 401

    with pytest.raises(BusinessRuleException) as revoked_error:
        services.refresh_access_token(None, successor["refresh_token"], redis_client)
    assert revoked_error.value.status_code == 401


def test_actual_lua_scripts_revoke_family_on_replay():
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    session_id = uuid4()
    user_id = uuid4()
    original_jti = uuid4()
    replacement_jti = uuid4()

    assert token_store.create_session(
        redis_client,
        session_id,
        user_id,
        original_jti,
        ttl_seconds=60,
    )
    assert token_store.rotate_session(
        redis_client,
        session_id,
        user_id,
        original_jti,
        replacement_jti,
        ttl_seconds=60,
    ) == token_store.RotationResult.ROTATED
    assert token_store.rotate_session(
        redis_client,
        session_id,
        user_id,
        original_jti,
        uuid4(),
        ttl_seconds=60,
    ) == token_store.RotationResult.REPLAYED
    assert token_store.rotate_session(
        redis_client,
        session_id,
        user_id,
        replacement_jti,
        uuid4(),
        ttl_seconds=60,
    ) == token_store.RotationResult.INVALID


def test_concurrent_refresh_has_one_winner_and_revokes_family(auth_services):
    redis_client = AtomicRedisFake()
    original = services.login_user(None, "user@example.com", "password", redis_client)

    def refresh():
        try:
            return services.refresh_access_token(
                None,
                original["refresh_token"],
                redis_client,
            )
        except BusinessRuleException as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: refresh(), range(2)))

    successes = [result for result in results if isinstance(result, dict)]
    failures = [result for result in results if isinstance(result, BusinessRuleException)]
    assert len(successes) == 1
    assert len(failures) == 1

    with pytest.raises(BusinessRuleException):
        services.refresh_access_token(None, successes[0]["refresh_token"], redis_client)


def test_logout_only_revokes_selected_session(auth_services):
    redis_client = AtomicRedisFake()
    first = services.login_user(None, "user@example.com", "password", redis_client)
    second = services.login_user(None, "user@example.com", "password", redis_client)

    services.logout(first["refresh_token"], redis_client)

    with pytest.raises(BusinessRuleException):
        services.refresh_access_token(None, first["refresh_token"], redis_client)
    assert services.refresh_access_token(None, second["refresh_token"], redis_client)


def test_auth_fails_closed_when_redis_is_unavailable(auth_services):
    with pytest.raises(BusinessRuleException) as error:
        services.login_user(
            None,
            "user@example.com",
            "password",
            AtomicRedisFake(unavailable=True),
        )

    assert error.value.status_code == 503
    assert error.value.error_code == "AUTH_STORE_UNAVAILABLE"


def test_registration_never_outputs_password(monkeypatch, caplog, capsys):
    password = "NeverLogMe123"
    created_user = SimpleNamespace(user_id=uuid4())

    class FakeDatabase:
        def add(self, user):
            created_user.email = user.email

        def commit(self):
            return None

        def refresh(self, user):
            user.user_id = created_user.user_id

    monkeypatch.setattr(services, "get_user_by_email", lambda *args: None)
    monkeypatch.setattr(services, "hash_password", lambda value: "hashed")
    user_create = SimpleNamespace(
        email="new@example.com",
        name="New User",
        password=password,
    )

    with caplog.at_level(logging.INFO):
        services.register_user(FakeDatabase(), user_create)

    captured = capsys.readouterr()
    assert password not in captured.out
    assert password not in captured.err
    assert password not in caplog.text