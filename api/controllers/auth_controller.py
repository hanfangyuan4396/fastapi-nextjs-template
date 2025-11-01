from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response
from fastapi.concurrency import run_in_threadpool

from schemas.auth import LoginRequest, LoginResponse
from services.auth_service import AuthService
from utils.config import settings
from utils.db import DbSession

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: DbSession = None):
    service = AuthService()
    result = await run_in_threadpool(
        lambda: service.login(
            db=db,
            username=payload.username,
            password=payload.password,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            # device_id 需前端提供或从既有 Cookie 读取，后端无法可靠自生成
            # 可后续通过自定义请求头/Cookie 传入
        )
    )

    # 成功则设置 refresh_token Cookie
    if result.get("code") == 0 and result.get("data"):
        data = result["data"]
        refresh_token: str | None = data.pop("refresh_token", None)
        refresh_expires_at: int | None = data.pop("refresh_expires_at", None)
        if refresh_token and refresh_expires_at:
            # 过期与 Max-Age，7 天（由配置与令牌一致）
            max_age = settings.REFRESH_TOKEN_EXPIRES_DAYS * 24 * 3600
            expires_dt = datetime.fromtimestamp(refresh_expires_at, UTC)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=max_age,
                expires=expires_dt,
                path="/",
            )
            # access_token 通过 JSON 返回由前端放内存并带 Authorization 使用
            # 避免将 access_token 放入 Cookie 增加 CSRF 面

    return result


@router.post("/auth/refresh", response_model=LoginResponse)
async def refresh(request: Request, response: Response, db: DbSession = None):
    service = AuthService()
    cookie_token = request.cookies.get("refresh_token")
    result = await run_in_threadpool(
        lambda: service.refresh(
            db=db,
            refresh_token=cookie_token,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )

    if result.get("code") == 0 and result.get("data"):
        data = result["data"]
        refresh_token: str | None = data.pop("refresh_token", None)
        refresh_expires_at: int | None = data.pop("refresh_expires_at", None)
        if refresh_token and refresh_expires_at:
            max_age = settings.REFRESH_TOKEN_EXPIRES_DAYS * 24 * 3600
            expires_dt = datetime.fromtimestamp(refresh_expires_at, UTC)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=max_age,
                expires=expires_dt,
                path="/",
            )

    return result
