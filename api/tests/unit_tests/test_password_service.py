from __future__ import annotations

import pytest

from core.security import verify_password
from services.email_verification_service import EmailVerificationService
from services.password_service import PasswordService
from tests.helpers import async_create_user


@pytest.mark.asyncio
async def test_change_password_success(async_db_session) -> None:
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
