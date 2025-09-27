from typing import Any

from fastapi import APIRouter, Request

from services.echo_service import EchoService

router = APIRouter()


@router.get("/echo")
async def echo_get(request: Request) -> dict[str, Any]:
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    echo_service = EchoService()
    return echo_service.build_echo_get_response(
        method=request.method,
        url=str(request.url),
        headers=headers,
        query_params=query_params,
    )
