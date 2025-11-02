from __future__ import annotations

from models import RefreshToken, User
from services.auth_service import AuthService
from tests.utils import create_expired_refresh_token, create_user, persist_refresh


def _create_user(db, username: str, password: str) -> User:  # 兼容旧签名
    return create_user(db, username, password)


def _persist_refresh(db, user: User) -> tuple[str, RefreshToken]:
    return persist_refresh(db, user)


# 服务层：logout 撤销整个家族（从根令牌测试）
def test_logout_revokes_family_from_root(db_session) -> None:
    user = _create_user(db_session, "lo1", "pw")
    token, rt = _persist_refresh(db_session, user)

    service = AuthService()
    result = service.logout(db=db_session, refresh_token=token)

    assert result["code"] == 0

    db_session.expire_all()
    stored = db_session.query(RefreshToken).filter(RefreshToken.jti == rt.jti).first()
    assert stored is not None
    assert stored.revoked is True


# 服务层：无效/缺失令牌时登出为幂等成功
def test_logout_is_idempotent_on_invalid_or_missing_token(db_session) -> None:
    service = AuthService()
    ok1 = service.logout(db=db_session, refresh_token=None)
    ok2 = service.logout(db=db_session, refresh_token="this-is-not-jwt")
    assert ok1["code"] == 0
    assert ok2["code"] == 0


# 服务层：过期但签名正确的 refresh 也应能定位并撤销家族
def test_logout_with_expired_token_still_revokes_family(db_session) -> None:
    user = _create_user(db_session, "lo2", "pw")
    expired_token, _ = create_expired_refresh_token(db_session, user)
    service = AuthService()
    result = service.logout(db=db_session, refresh_token=expired_token)
    assert result["code"] == 0

    db_session.expire_all()
    stored = db_session.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
    assert stored is not None
    assert stored.revoked is True
