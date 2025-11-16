from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    """
    获取客户端 IP：
    1. 优先从 X-Forwarded-For（可能包含多个 IP，取第一个）
    2. 其次从 X-Real-IP
    3. 最后回退到 request.client.host
    """
    # Starlette/ FastAPI 的 headers 大小写不敏感，这里统一用小写访问
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # 形如 "client, proxy1, proxy2" → 取第一个非空
        first_ip = x_forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        ip = x_real_ip.strip()
        if ip:
            return ip

    if request.client:
        return request.client.host

    return None
