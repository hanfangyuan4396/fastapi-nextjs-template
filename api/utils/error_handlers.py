import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger()


def error_response(message: str, code: int = 500) -> dict:
    return {"code": code, "message": message}


async def global_exception_handler(request: Request, e: Exception):
    logger.exception("Unhandled exception: %s", e)
    return JSONResponse(status_code=500, content=error_response(str(e)))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, global_exception_handler)
