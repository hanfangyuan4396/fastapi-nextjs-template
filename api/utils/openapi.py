from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def create_custom_openapi(app: FastAPI) -> None:
    """
    为 FastAPI 应用挂载自定义 OpenAPI：
    - 增加全局 Bearer Authorization 配置
    - 让 Swagger UI 出现 Authorize 按钮并支持填写 Authorization 头
    """

    def custom_openapi():
        if getattr(app, "openapi_schema", None):
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        openapi_schema.setdefault("components", {})
        openapi_schema["components"].setdefault("securitySchemes", {})

        # 定义一个 BearerAuth 安全方案，用于在 Swagger UI 中填写 Authorization 头
        openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        # 让所有接口在文档层面默认携带此安全要求（仅影响文档展示，不会强制校验）
        openapi_schema["security"] = [{"BearerAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
