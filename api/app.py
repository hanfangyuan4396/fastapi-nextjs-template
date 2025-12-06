import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.auth_controller import router as auth_router

# from controller.admin_services_controller import router as admin_services_router  # 暂时禁用：缺少 token 验证
from controllers.docs_controller import router as docs_router
from controllers.echo_controller import router as echo_router
from controllers.students_controller import router as students_router
from utils import register_exception_handlers
from utils.config import settings
from utils.logging import get_logger, init_logging
from utils.openapi import create_custom_openapi

API_PREFIX = "/api"

app = FastAPI(
    title="FastAPI Demo",
    description="A simple FastAPI application",
    version="1.0.0",
    # 关闭默认 docs/redoc/openapi，改用自定义并加上 Basic 认证
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

init_logging(settings.LOG_LEVEL)
logger = get_logger()

# 加载 .env 已由 utils.config.Settings 完成

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # 允许跨域请求携带 cookie、Authorization 等
    allow_methods=["*"],
    allow_headers=["*"],
)

# 装配全局异常处理器
register_exception_handlers(app)

# 挂载自定义 OpenAPI（增加全局 BearerAuth 安全配置）
create_custom_openapi(app)

# 挂载路由
app.include_router(echo_router, prefix=API_PREFIX)
app.include_router(students_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(docs_router, prefix=API_PREFIX)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
