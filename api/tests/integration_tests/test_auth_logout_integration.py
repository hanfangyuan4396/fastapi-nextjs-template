from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import RefreshToken, User
from tests.utils import create_user


def _create_user(db: Session, username: str, password: str, *, is_active: bool = True) -> User:  # 保持原签名
    return create_user(db, username, password, is_active=is_active)


# 登出后：删除 Cookie；随后刷新应失败（缺少 refresh_token）。
def test_logout_endpoint_clears_cookie_and_refresh_fails(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "lou", "pw")

    r1 = client.post("/api/auth/login", json={"username": "lou", "password": "pw"})
    assert r1.status_code == 200
    old_cookie = r1.cookies.get("refresh_token")
    assert old_cookie

    r2 = client.post("/api/auth/logout")
    assert r2.status_code == 200
    body = r2.json()
    assert body["code"] == 0

    # Cookie 被清除
    assert client.cookies.get("refresh_token") is None

    # 刷新将失败（因为缺少 cookie）
    r3 = client.post("/api/auth/refresh")
    assert r3.status_code == 200
    assert r3.json()["code"] != 0


# 登出会撤销家族：客户端若缓存旧 cookie 并再次尝试刷新，将得到撤销错误码；DB 中家族被撤销。
def test_logout_endpoint_revokes_family_then_old_cookie_refresh_fails(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "lov", "pw")

    r1 = client.post("/api/auth/login", json={"username": "lov", "password": "pw"})
    assert r1.status_code == 200
    cookie_before = r1.cookies.get("refresh_token")
    assert cookie_before

    r2 = client.post("/api/auth/logout")
    assert r2.status_code == 200
    assert r2.json()["code"] == 0

    # 人为设置回旧的 cookie 并尝试刷新，应返回撤销类错误
    client.cookies.set("refresh_token", cookie_before)
    r3 = client.post("/api/auth/refresh")
    assert r3.status_code == 200
    assert r3.json()["code"] in (40112, 40110)  # 撤销或无效

    db_session.expire_all()
    tokens = db_session.query(RefreshToken).all()
    assert len(tokens) >= 1
    assert all(t.revoked for t in tokens)
