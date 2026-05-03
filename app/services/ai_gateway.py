import logging
from time import perf_counter

import httpx

from app.config import get_settings

logger = logging.getLogger("deeptraining.ai_gateway")


class AIGatewayError(RuntimeError):
    pass


async def call_ai_gateway(
    *,
    message: str,
    response_mode: str | None = None,
    temperature: float = 0.3,
) -> str:
    settings = get_settings()
    mode = response_mode or settings.ai_default_response_mode or "fast"

    if not settings.ai_gateway_api_key:
        raise AIGatewayError("AI_GATEWAY_API_KEY is not configured")

    base_url = settings.ai_gateway_base_url.rstrip("/")
    endpoint = f"{base_url}/v1/chat"
    payload = {
        "message": message,
        "temperature": temperature,
        "response_mode": mode,
    }
    headers = {
        "Authorization": f"Bearer {settings.ai_gateway_api_key}",
        "Content-Type": "application/json",
    }

    start = perf_counter()
    try:
        async with httpx.AsyncClient(timeout=settings.ai_gateway_timeout_seconds) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
        elapsed_ms = round((perf_counter() - start) * 1000)
    except httpx.TimeoutException as exc:
        logger.warning("ai_gateway timeout mode=%s duration_ms=%s", mode, round((perf_counter() - start) * 1000))
        raise AIGatewayError("AI gateway request timed out") from exc
    except httpx.HTTPError as exc:
        logger.exception("ai_gateway transport_error mode=%s", mode)
        raise AIGatewayError("AI gateway transport error") from exc

    if response.status_code >= 400:
        logger.warning("ai_gateway http_error status=%s mode=%s duration_ms=%s", response.status_code, mode, elapsed_ms)
        raise AIGatewayError(f"AI gateway returned HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("ai_gateway invalid_json status=%s mode=%s duration_ms=%s", response.status_code, mode, elapsed_ms)
        raise AIGatewayError("AI gateway returned invalid JSON") from exc

    content = (data.get("response") or "").strip()
    if not content:
        logger.warning("ai_gateway empty_response status=%s mode=%s duration_ms=%s", response.status_code, mode, elapsed_ms)
        raise AIGatewayError("AI gateway returned an empty response")

    logger.info(
        "ai_gateway ok status=%s mode=%s duration_ms=%s response_chars=%s",
        response.status_code,
        mode,
        elapsed_ms,
        len(content),
    )
    return content
