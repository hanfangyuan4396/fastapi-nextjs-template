from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response
from fastapi.concurrency import run_in_threadpool

from schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterVerifyAndCreateRequest,
    SendRegisterCodeRequest,
    SendRegisterCodeResponse,
)
from services.auth_service import AuthService
from services.email_verification_service import EmailVerificationService
from services.registration_service import RegistrationService
from utils.config import settings
from utils.db import AsyncDbSession, DbSession

router = APIRouter()


@router.post("/auth/register/send-code", response_model=SendRegisterCodeResponse)
async def send_register_code(payload: SendRegisterCodeRequest, request: Request, db: AsyncDbSession = None):
    service = EmailVerificationService()

    client_ip = request.client.host if request.client else None
    result = await service.send_register_code(
        db=db,
        email=str(payload.email),
        client_ip=client_ip,
    )
    return result


@router.post("/auth/register/verify-and-create", response_model=LoginResponse)
async def register_verify_and_create(
    payload: RegisterVerifyAndCreateRequest,
    request: Request,
    response: Response,
    db: AsyncDbSession = None,
):
    service = RegistrationService()

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = await service.register_with_email_code(
        db=db,
        email=str(payload.email),
        code=payload.code,
        password=payload.password,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    # 成功则设置 refresh_token Cookie（复用登录逻辑）
    if result.get("code") == 0 and result.get("data"):
        data = result["data"]
        refresh_token: str | None = data.pop("refresh_token", None)
        refresh_expires_at: int | None = data.pop("refresh_expires_at", None)
        if refresh_token and refresh_expires_at:
            max_age = settings.REFRESH_TOKEN_EXPIRES_MINUTES * 60
            expires_dt = datetime.fromtimestamp(refresh_expires_at, UTC)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,  # TODO: 生产环境需要设置为True，使用https，为了通过测试先设置为False
                samesite="lax",
                max_age=max_age,
                expires=expires_dt,
                path="/",
            )

    return result


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
            # 过期与 Max-Age（由配置与令牌一致，分钟→秒）
            max_age = settings.REFRESH_TOKEN_EXPIRES_MINUTES * 60
            expires_dt = datetime.fromtimestamp(refresh_expires_at, UTC)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,  # TODO: 生产环境需要设置为True，使用https，为了通过测试先设置为False
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
            max_age = settings.REFRESH_TOKEN_EXPIRES_MINUTES * 60
            expires_dt = datetime.fromtimestamp(refresh_expires_at, UTC)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,  # TODO: 生产环境需要设置为True，使用https，为了通过测试先设置为False
                samesite="lax",
                max_age=max_age,
                expires=expires_dt,
                path="/",
            )

    return result


@router.post("/auth/logout", response_model=LoginResponse)
async def logout(request: Request, response: Response, db: DbSession = None):
    service = AuthService()
    cookie_token = request.cookies.get("refresh_token")
    result = await run_in_threadpool(
        lambda: service.logout(
            db=db,
            refresh_token=cookie_token,
        )
    )

    # 无论服务处理结果如何，都清理 Cookie（幂等）
    try:
        response.delete_cookie(key="refresh_token", path="/")
    except Exception:
        # 保底：若底层实现不支持 delete_cookie，可用 set_cookie 覆盖过期
        response.set_cookie(
            key="refresh_token",
            value="",
            max_age=0,
            expires=0,
            path="/",
        )

    return result
