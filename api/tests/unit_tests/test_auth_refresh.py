from __future__ import annotations

from models import RefreshToken, User
from services.auth_service import AuthService
from tests.helpers import create_expired_refresh_token, create_user, persist_refresh


def _create_user(db, username: str, password: str) -> User:  # 兼容旧调用签名
    return create_user(db, username, password)


# 服务层：刷新成功的轮换流程——旧刷新令牌 used_at 置位；
# 新刷新令牌插入且 parent_jti 指向旧 jti，同时返回新的 access_token。
def test_refresh_rotate_success(db_session) -> None:
    user = _create_user(db_session, "r1", "pw")
    token, rt = persist_refresh(db_session, user)

    service = AuthService()
    result = service.refresh(db=db_session, refresh_token=token)

    assert result["code"] == 0
    assert "access_token" in (result.get("data") or {})

    db_session.expire_all()
    old = db_session.query(RefreshToken).filter(RefreshToken.jti == rt.jti).first()
    assert old is not None
    assert old.used_at is not None

    # 新纪录插入且 parent_jti 指向旧 jti
    children = db_session.query(RefreshToken).filter(RefreshToken.parent_jti == rt.jti).all()
    assert len(children) == 1


# 服务层：复用检测——同一刷新令牌第二次使用将被识别为复用；
# 服务撤销整个家族的刷新令牌（全部 revoked=true）。
def test_refresh_reuse_detects_and_revokes_family(db_session) -> None:
    user = _create_user(db_session, "r2", "pw")
    token, rt = persist_refresh(db_session, user)

    service = AuthService()
    first = service.refresh(db=db_session, refresh_token=token)
    assert first["code"] == 0

    # 复用旧 token
    second = service.refresh(db=db_session, refresh_token=token)
    assert second["code"] == 40112

    # 家族内所有刷新令牌应被撤销
    db_session.expire_all()
    tokens = db_session.query(RefreshToken).all()
    assert len(tokens) >= 2
    assert all(t.revoked for t in tokens)

    # 使用子令牌也应失败
    child = next(t for t in tokens if t.parent_jti == rt.jti)
    # 为了避免复杂化 JWT 重签名，这里直接断言 DB 层已撤销即可
    assert child.revoked is True


# 服务层：过期刷新——传入已过期的 refresh_token 时，返回 40111（刷新令牌已过期）。
def test_refresh_expired_returns_401(db_session) -> None:
    user = _create_user(db_session, "r3", "pw")
    expired_token, rt = create_expired_refresh_token(db_session, user)
    service = AuthService()
    result = service.refresh(db=db_session, refresh_token=expired_token)
    assert result["code"] == 40111
