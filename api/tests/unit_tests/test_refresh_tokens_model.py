from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from models.refresh_tokens import RefreshToken
from models.users import User


def _create_user(db_session) -> User:
    u = User(username="rt_user", password_hash="hashed:pw")
    db_session.add(u)
    db_session.commit()
    return u


def test_refresh_token_insert_and_query(db_session):
    user = _create_user(db_session)

    now = datetime.now(UTC)
    rt = RefreshToken(
        jti="jti-001",
        parent_jti=None,
        user_id=user.id,
        issued_at=now,
        expires_at=now + timedelta(hours=1),
        device_id="dev1",
        ip="127.0.0.1",
        user_agent="pytest-agent",
    )
    db_session.add(rt)
    db_session.commit()

    got: RefreshToken = db_session.query(RefreshToken).filter(RefreshToken.jti == "jti-001").one()

    assert got.user_id == user.id
    assert got.parent_jti is None
    assert got.revoked is False
    assert got.used_at is None
    assert got.device_id == "dev1"
    assert got.ip == "127.0.0.1"
    assert got.user_agent == "pytest-agent"
    assert got.is_expired(now=now) is False


def test_refresh_token_jti_unique(db_session):
    user = _create_user(db_session)
    now = datetime.now(UTC)
    for _ in range(2):
        rt = RefreshToken(
            jti="dup-jti",
            parent_jti=None,
            user_id=user.id,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        db_session.add(rt)
        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            break
    else:
        pytest.fail("jti unique constraint not enforced")


def test_is_expired_checks_expires_at(db_session):
    user = _create_user(db_session)
    now = datetime.now(UTC)

    rt_future = RefreshToken(
        jti="future-jti",
        user_id=user.id,
        issued_at=now,
        expires_at=now + timedelta(minutes=1),
    )
    rt_past = RefreshToken(
        jti="past-jti",
        user_id=user.id,
        issued_at=now - timedelta(minutes=2),
        expires_at=now - timedelta(minutes=1),
    )
    db_session.add_all([rt_future, rt_past])
    db_session.commit()

    assert rt_future.is_expired(now=now) is False
    assert rt_past.is_expired(now=now) is True
