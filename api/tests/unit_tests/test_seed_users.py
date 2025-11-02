from datetime import UTC, datetime, timedelta

from core.security import verify_password
from models.users import User
from utils.seed_users import upsert_user


def test_seed_creates_admin_and_user(db_session):
    user_admin, action_admin = upsert_user(db_session, "admin", "123456", "admin")
    user_user, action_user = upsert_user(db_session, "user", "123456", "user")
    db_session.commit()

    assert action_admin == "created"
    assert action_user == "created"

    got_admin = db_session.query(User).filter(User.username == "admin").one()
    got_user = db_session.query(User).filter(User.username == "user").one()

    assert got_admin.role == "admin"
    assert got_user.role == "user"
    assert got_admin.is_active is True
    assert got_user.is_active is True
    assert verify_password("123456", got_admin.password_hash) is True
    assert verify_password("123456", got_user.password_hash) is True


def test_seed_idempotent_skips_when_no_change(db_session):
    """
    Verifies that calling upsert_user again with identical username, password, and role
    is idempotent and preserves the stored password hash.

    Creates an "admin" user, records its password hash, runs upsert_user with the same
    credentials a second time, and asserts that the operation reports "skipped" and the
    user's password_hash remains unchanged.
    """
    upsert_user(db_session, "admin", "123456", "admin")
    db_session.commit()
    before = db_session.query(User).filter(User.username == "admin").one()
    hash_before = before.password_hash

    _, action = upsert_user(db_session, "admin", "123456", "admin")
    db_session.commit()

    after = db_session.query(User).filter(User.username == "admin").one()
    assert action == "skipped"
    assert after.password_hash == hash_before


def test_seed_resets_lock_and_failures(db_session):
    """
    Verifies that upsert_user clears failed login attempts and lock state when updating
    an existing account.

    Creates a user, simulates a locked/failed-login state by setting `failed_login_attempts`
    and `lock_until`, calls `upsert_user` with the same credentials, and asserts the
    operation reports `"updated"` and that `failed_login_attempts` is reset to 0 and
    `lock_until` is cleared.
    """
    user, _ = upsert_user(db_session, "user", "123456", "user")
    db_session.commit()

    # 模拟锁定与失败计数
    user.failed_login_attempts = 5
    user.lock_until = datetime.now(UTC) + timedelta(hours=1)
    db_session.commit()

    _, action = upsert_user(db_session, "user", "123456", "user")
    db_session.commit()

    got = db_session.query(User).filter(User.username == "user").one()
    assert action == "updated"
    assert got.failed_login_attempts == 0
    assert got.lock_until is None


def test_seed_updates_role(db_session):
    upsert_user(db_session, "bob", "123456", "user")
    db_session.commit()

    _, action = upsert_user(db_session, "bob", "123456", "admin")
    db_session.commit()

    got = db_session.query(User).filter(User.username == "bob").one()
    assert action == "updated"
    assert got.role == "admin"
