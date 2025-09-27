from typing import Any

from utils.logging import get_logger

logger = get_logger()


class EchoService:
    def build_echo_get_response(
        self,
        method: str,
        url: str,
        headers: dict[str, Any],
        query_params: dict[str, Any],
    ) -> dict[str, Any]:
        logger.debug(
            "method=%s url=%s headers=%s query=%s",
            method,
            url,
            headers,
            query_params,
        )
        return {
            "method": "GET",
            "headers": headers,
            "query": query_params,
        }
