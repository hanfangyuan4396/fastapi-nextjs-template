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
