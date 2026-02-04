# 参考实现：用户密码相关后端功能

以下代码来自当前项目后端实现，用于复用“修改密码 + 忘记密码/验证码重置”功能。

## 1. Schemas

文件：`api/schemas/auth.py`

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=200)


class LoginResponse(BaseModel):
    code: int
    message: str
    data: dict[str, Any] | None = None


class SendRegisterCodeRequest(BaseModel):
    email: EmailStr


class SendRegisterCodeResponse(BaseModel):
    code: int
    message: str
    data: dict[str, Any] | None = None


class RegisterVerifyAndCreateRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=1, max_length=10)
    # 密码复杂度：这里只做长度约束，后续可根据需要扩展为必须包含数字/字母等
    password: str = Field(..., min_length=6, max_length=200)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=200)
    new_password: str = Field(..., min_length=6, max_length=200)
    confirm_password: str = Field(..., min_length=6, max_length=200)


class SendResetCodeRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=1, max_length=10)
    new_password: str = Field(..., min_length=6, max_length=200)
    confirm_password: str = Field(..., min_length=6, max_length=200)


class BasicResponse(BaseModel):
    code: int
    message: str
    data: dict[str, Any] | None = None
```

## 2. 密码服务

文件：`api/services/password_service.py`

```python
from __future__ import annotations

from typing import Any

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password
from models import User
from services.email_verification_service import EmailVerificationService
from utils.logging import get_logger

logger = get_logger()


class PasswordService:
    """密码相关业务逻辑：修改密码、忘记密码重置。"""

    async def change_password(
        self,
        *,
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> dict[str, Any]:
        if not old_password or not new_password or not confirm_password:
            return {"code": 42203, "message": "密码不能为空"}

        if new_password != confirm_password:
            return {"code": 42204, "message": "两次新密码不一致"}

        if len(new_password) < 6:
            return {"code": 42205, "message": "新密码长度至少 6 位"}

        if not verify_password(old_password, user.password_hash):
            return {"code": 40010, "message": "旧密码错误"}

        try:
            user.password_hash = hash_password(new_password)
            db.add(user)
            await db.commit()
            return {"code": 0, "message": "ok"}
        except Exception:
            await db.rollback()
            logger.exception("change password failed")
            return {"code": 50030, "message": "修改密码失败"}

    async def reset_password(
        self,
        *,
        db: AsyncSession,
        email: str,
        code: str,
        new_password: str,
        confirm_password: str,
    ) -> dict[str, Any]:
        try:
            valid_email = TypeAdapter(EmailStr).validate_python(email)
        except ValidationError:
            return {"code": 42201, "message": "邮箱格式不合法"}

        if not code:
            return {"code": 42202, "message": "验证码格式不合法"}

        if not new_password or not confirm_password:
            return {"code": 42203, "message": "密码不能为空"}

        if new_password != confirm_password:
            return {"code": 42204, "message": "两次新密码不一致"}

        if len(new_password) < 6:
            return {"code": 42205, "message": "新密码长度至少 6 位"}

        email_service = EmailVerificationService()
        otp_result = await email_service.verify_and_consume_code(
            email=str(valid_email),
            code=code,
            scene=EmailVerificationService.SCENE_RESET_PASSWORD,
        )
        if otp_result.get("code") != 0:
            return otp_result

        try:
            stmt = select(User).where(User.username == str(valid_email))
            result = await db.execute(stmt)
            user: User | None = result.scalars().first()
            if user is None or not user.is_active:
                return {"code": 40401, "message": "邮箱不存在"}
        except Exception:
            logger.exception("check user for reset password failed")
            return {"code": 50031, "message": "重置密码失败"}

        try:
            user.password_hash = hash_password(new_password)
            db.add(user)
            await db.commit()
            return {"code": 0, "message": "ok"}
        except Exception:
            await db.rollback()
            logger.exception("reset password failed")
            return {"code": 50031, "message": "重置密码失败"}
```

## 3. 邮件验证码服务扩展（忘记密码场景）

文件：`api/services/email_verification_service.py`

```python
class EmailVerificationService:
    # 业务场景常量，预留未来扩展（如 reset_password）
    SCENE_REGISTER = "register"
    SCENE_RESET_PASSWORD = "reset_password"

    async def send_reset_password_code(
        self,
        *,
        db: AsyncSession,
        email: str,
        client_ip: str | None = None,
    ) -> dict[str, Any]:
        try:
            valid_email = TypeAdapter(EmailStr).validate_python(email)
        except ValidationError:
            return {"code": 42201, "message": "邮箱格式不合法"}

        try:
            stmt = select(User).where(User.username == str(valid_email))
            result = await db.execute(stmt)
            existing: User | None = result.scalars().first()
            if existing is None or not existing.is_active:
                return {"code": 40401, "message": "邮箱不存在"}
        except Exception:
            logger.exception("check existing user for reset password failed")
            return {"code": 50020, "message": "检查邮箱状态失败"}

        r = get_redis()

        email_key = self._build_rate_email_key(str(valid_email))
        try:
            email_count = await r.incr(email_key)
            if email_count == 1:
                await r.expire(email_key, self.RATE_LIMIT_WINDOW_SECONDS)
            if email_count > settings.EMAIL_VERIFICATION_RATE_LIMIT_PER_EMAIL:
                return {"code": 42901, "message": "验证码发送过于频繁，请稍后再试"}
        except Exception:
            logger.exception("email-based rate limit failed")
            return {"code": 50021, "message": "发送验证码失败"}

        if client_ip:
            ip_key = self._build_rate_ip_key(client_ip)
            try:
                ip_count = await r.incr(ip_key)
                if ip_count == 1:
                    await r.expire(ip_key, self.RATE_LIMIT_WINDOW_SECONDS)
                if ip_count > settings.EMAIL_VERIFICATION_RATE_LIMIT_PER_IP:
                    return {"code": 42902, "message": "当前 IP 请求过于频繁，请稍后再试"}
            except Exception:
                logger.exception("ip-based rate limit failed")
                return {"code": 50021, "message": "发送验证码失败"}

        code = self._generate_numeric_code(6)
        code_hash = hash_password(code)

        ttl_seconds = settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES * 60
        now = datetime.now(UTC)

        code_key = self._build_code_key(scene=self.SCENE_RESET_PASSWORD, email=str(valid_email))

        try:
            await r.hset(
                code_key,
                mapping={
                    "code_hash": code_hash,
                    "scene": self.SCENE_RESET_PASSWORD,
                    "created_at": now.isoformat(),
                    "used": "0",
                    "failed_attempts": "0",
                    "ip": client_ip or "",
                },
            )
            await r.expire(code_key, ttl_seconds)
        except Exception:
            logger.exception("store verification code in redis failed")
            return {"code": 50021, "message": "发送验证码失败"}

        try:
            await asyncio.to_thread(
                send_verification_email,
                str(valid_email),
                code,
                settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES,
            )
        except EmailNotConfiguredError as err:
            logger.exception("email verification config not set correctly")
            return {"code": 50022, "message": str(err)}
        except Exception:
            logger.exception("send verification email failed")
            return {"code": 50021, "message": "发送验证码失败"}

        return {"code": 0, "message": "ok", "data": {"expires_in": ttl_seconds}}

    async def verify_and_consume_code(
        self,
        *,
        email: str,
        code: str,
        scene: str = SCENE_REGISTER,
    ) -> dict[str, Any]:
        ...
        code_key = self._build_code_key(scene=scene, email=str(valid_email))
        ...
```

## 4. 控制器路由

文件：`api/controllers/auth_controller.py`

```python
@router.post("/auth/password/change", response_model=BasicResponse)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    db: AsyncDbSession = None,
):
    service = PasswordService()
    result = await service.change_password(
        db=db,
        user=current_user,
        old_password=payload.old_password,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
    )
    return result


@router.post("/auth/password/reset/send-code", response_model=SendRegisterCodeResponse)
async def send_reset_code(payload: SendResetCodeRequest, request: Request, db: AsyncDbSession = None):
    service = EmailVerificationService()
    client_ip = get_client_ip(request)
    result = await service.send_reset_password_code(
        db=db,
        email=str(payload.email),
        client_ip=client_ip,
    )
    return result


@router.post("/auth/password/reset/confirm", response_model=BasicResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncDbSession = None):
    service = PasswordService()
    result = await service.reset_password(
        db=db,
        email=str(payload.email),
        code=payload.code,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
    )
    return result
```

## 5. 当前用户信息接口

文件：`api/schemas/auth.py`

```python
class UserProfile(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool
    token_version: int


class MeResponse(BaseModel):
    code: int
    message: str
    data: UserProfile | None = None
```

文件：`api/controllers/auth_controller.py`

```python
@router.get("/auth/me", response_model=MeResponse)
async def me(current_user: CurrentUser):
    return {"code": 0, "message": "ok", "data": current_user.to_safe_dict()}
```

## 6. 相关测试

### 6.1 邮箱验证码服务测试（新增 reset 场景）

文件：`api/tests/unit_tests/test_email_verification_service.py`

```python
@pytest.mark.asyncio
async def test_send_reset_password_code_success(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    # 目的：忘记密码验证码发送成功并写入 reset_password 场景的 Redis key
    from models import User

    user = User(username="reset@example.com", password_hash="x", role="user", is_active=True)
    async_db_session.add(user)
    await async_db_session.commit()

    service = EmailVerificationService()
    resp = await service.send_reset_password_code(
        db=async_db_session,
        email="reset@example.com",
        client_ip=None,
    )

    assert resp["code"] == 0

    code_key = (
        f"{EmailVerificationService.KEY_PREFIX_CODE}:{EmailVerificationService.SCENE_RESET_PASSWORD}:reset@example.com"
    )
    stored = await fake_redis.hgetall(code_key)
    assert stored.get("scene") == EmailVerificationService.SCENE_RESET_PASSWORD
    assert len(noop_email_sender) == 1


@pytest.mark.asyncio
async def test_send_reset_password_code_email_not_found(async_db_session, fake_redis: FakeRedis, noop_email_sender):
    # 目的：忘记密码邮箱不存在时返回错误且不发送邮件
    service = EmailVerificationService()
    resp = await service.send_reset_password_code(
        db=async_db_session,
        email="missing@example.com",
        client_ip=None,
    )

    assert resp["code"] == 40401
    assert noop_email_sender == []
```

### 6.2 密码服务测试

文件：`api/tests/unit_tests/test_password_service.py`

```python
from __future__ import annotations

import pytest

from core.security import verify_password
from services.email_verification_service import EmailVerificationService
from services.password_service import PasswordService
from tests.helpers import async_create_user


@pytest.mark.asyncio
async def test_change_password_success(async_db_session) -> None:
    # 目的：旧密码正确且新密码合规时可成功修改
    user = await async_create_user(async_db_session, "user1@example.com", "oldpass")
    service = PasswordService()

    result = await service.change_password(
        db=async_db_session,
        user=user,
        old_password="oldpass",
        new_password="newpass1",
        confirm_password="newpass1",
    )

    assert result["code"] == 0
    await async_db_session.refresh(user)
    assert verify_password("newpass1", user.password_hash)


@pytest.mark.asyncio
async def test_change_password_wrong_old(async_db_session) -> None:
    # 目的：旧密码错误时返回错误码
    user = await async_create_user(async_db_session, "user2@example.com", "oldpass")
    service = PasswordService()

    result = await service.change_password(
        db=async_db_session,
        user=user,
        old_password="badpass",
        new_password="newpass1",
        confirm_password="newpass1",
    )

    assert result["code"] == 40010


@pytest.mark.asyncio
async def test_change_password_mismatch(async_db_session) -> None:
    # 目的：两次新密码不一致时返回错误码
    user = await async_create_user(async_db_session, "user3@example.com", "oldpass")
    service = PasswordService()

    result = await service.change_password(
        db=async_db_session,
        user=user,
        old_password="oldpass",
        new_password="newpass1",
        confirm_password="newpass2",
    )

    assert result["code"] == 42204


@pytest.mark.asyncio
async def test_change_password_too_short(async_db_session) -> None:
    # 目的：新密码长度不足时返回错误码
    user = await async_create_user(async_db_session, "user4@example.com", "oldpass")
    service = PasswordService()

    result = await service.change_password(
        db=async_db_session,
        user=user,
        old_password="oldpass",
        new_password="short",
        confirm_password="short",
    )

    assert result["code"] == 42205


@pytest.mark.asyncio
async def test_reset_password_success(async_db_session, monkeypatch) -> None:
    # 目的：验证码通过后可成功重置密码
    user = await async_create_user(async_db_session, "reset1@example.com", "oldpass")
    service = PasswordService()

    async def _ok_verify(self, *, email: str, code: str, scene: str):
        return {"code": 0, "message": "ok"}

    monkeypatch.setattr(
        EmailVerificationService,
        "verify_and_consume_code",
        _ok_verify,
    )

    result = await service.reset_password(
        db=async_db_session,
        email="reset1@example.com",
        code="123456",
        new_password="newpass1",
        confirm_password="newpass1",
    )

    assert result["code"] == 0
    await async_db_session.refresh(user)
    assert verify_password("newpass1", user.password_hash)


@pytest.mark.asyncio
async def test_reset_password_mismatch(async_db_session, monkeypatch) -> None:
    # 目的：两次新密码不一致时返回错误码
    await async_create_user(async_db_session, "reset2@example.com", "oldpass")
    service = PasswordService()

    async def _ok_verify(self, *, email: str, code: str, scene: str):
        return {"code": 0, "message": "ok"}

    monkeypatch.setattr(
        EmailVerificationService,
        "verify_and_consume_code",
        _ok_verify,
    )

    result = await service.reset_password(
        db=async_db_session,
        email="reset2@example.com",
        code="123456",
        new_password="newpass1",
        confirm_password="newpass2",
    )

    assert result["code"] == 42204
```
### 6.3 当前用户信息接口测试

文件：`api/tests/integration_tests/test_auth_me.py`

```python
@pytest.mark.asyncio
async def test_me_returns_current_user(async_client: AsyncClient, async_db_session: AsyncSession) -> None:
    # 目的：携带 access token 时返回当前用户信息
    await _create_user(async_db_session, "me@example.com", "secret")

    login_resp = await async_client.post("/api/auth/login", json={"username": "me@example.com", "password": "secret"})
    assert login_resp.status_code == 200
    body = login_resp.json()
    access_token = (body.get("data") or {}).get("access_token")
    assert access_token

    resp = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["code"] == 0
    assert payload["data"]["username"] == "me@example.com"
    assert payload["data"]["role"] == "user"


@pytest.mark.asyncio
async def test_me_requires_auth(async_client: AsyncClient) -> None:
    # 目的：未携带 token 时返回 401
    resp = await async_client.get("/api/auth/me")
    assert resp.status_code == 401
```
