from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from utils.config import settings

router = APIRouter()

# Swagger 文档访问账号密码（从环境变量 / 配置读取）
DOCS_USERNAME = settings.DOCS_USERNAME
DOCS_PASSWORD = settings.DOCS_PASSWORD

security = HTTPBasic()


def verify_docs_credentials(
    credentials: HTTPBasicCredentials = Depends(security),  # noqa: B008 - FastAPI 依赖注入的推荐写法
) -> None:
    """
    校验访问文档的用户名和密码。
    """
    correct_username = secrets.compare_digest(credentials.username, DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)

    if not (correct_username and correct_password):
        # 触发浏览器弹出 Basic Auth 登录框
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@router.get("/docs", include_in_schema=False)
async def custom_swagger_ui(
    _: None = Depends(verify_docs_credentials),
):
    """
    受 Basic Auth 保护的 Swagger UI。
    访问时浏览器会弹出用户名/密码输入框。
    """
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="FastAPI Demo - Docs",
    )


@router.get("/openapi.json", include_in_schema=False)
async def protected_openapi(
    request: Request,
    _: None = Depends(verify_docs_credentials),
):
    """
    同样对 OpenAPI schema 加 Basic Auth 保护，避免直接未授权访问 JSON。
    通过 request.app.openapi() 获取绑定在 FastAPI 实例上的自定义 OpenAPI。
    """
    return JSONResponse(request.app.openapi())
