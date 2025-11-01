import pytest
from sqlalchemy.exc import IntegrityError

from models.users import User


def test_create_user_defaults(db_session):
    u = User(username="alice", password_hash="hashed:xxx")
    db_session.add(u)
    db_session.commit()

    got = db_session.query(User).filter(User.username == "alice").one()
    assert got.role == "user"
    assert got.is_active is True
    assert got.token_version == 1
    assert got.failed_login_attempts == 0
    assert got.lock_until is None


def test_username_unique(db_session):
    u1 = User(username="bob", password_hash="hashed:yyy")
    db_session.add(u1)
    db_session.commit()

    u2 = User(username="bob", password_hash="hashed:zzz")
    db_session.add(u2)
    try:
        db_session.commit()
        # 如果能走到这里，说明唯一约束未生效
        pytest.fail("username unique constraint not enforced")
    except IntegrityError:
        db_session.rollback()
