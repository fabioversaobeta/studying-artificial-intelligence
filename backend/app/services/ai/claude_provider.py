"""Claude (Anthropic API) provider.

The only module of the project that touches the ``anthropic`` SDK. The import
is lazy and guarded so the app (and the fake provider) run without the
package, and the client is injectable so tests never hit the network.

Notes on the request shape (see the ``claude-api`` skill):
- structured output uses ``output_config.format`` with a JSON schema
  (``anthropic.transform_schema`` adapts a Pydantic schema to what the API
  accepts), not forced tool use (which current models reject);
- ``temperature`` is only sent when the caller sets it, because the newest
  models reject non-default sampling parameters;
- ``thinking`` is left at the model default; budget ``max_tokens`` for it;
- timeouts and bounded retries (429/5xx/connection) are delegated to the SDK
  client (``timeout`` / ``max_retries``), so wall-clock is bounded by
  ``timeout * (max_retries + 1)``.
"""

import time
from typing import Any

from app.services.ai.base import AIRequest, AIResponse, AIUsageInfo
from app.services.ai.errors import (
    AIError,
    AIProviderError,
    AIRateLimited,
    AIUnavailable,
)


def _import_sdk() -> Any:
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise AIUnavailable(
            "The 'anthropic' package is not installed (pip install 'anthropic>=1.0')"
        ) from exc
    return anthropic


class ClaudeProvider:
    name = "claude"

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            if not self._api_key:
                raise AIUnavailable("ANTHROPIC_API_KEY is not configured")
            sdk = _import_sdk()
            self._client = sdk.Anthropic(
                api_key=self._api_key,
                timeout=self._timeout,
                max_retries=self._max_retries,
            )
        return self._client

    def _build_params(self, request: AIRequest) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }
        if request.system:
            params["system"] = (
                [
                    {
                        "type": "text",
                        "text": request.system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
                if request.cache_system
                else request.system
            )
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.output_schema is not None:
            sdk = _import_sdk()
            params["output_config"] = {
                "format": {
                    "type": "json_schema",
                    "schema": sdk.transform_schema(request.output_schema),
                }
            }
        return params

    def complete(self, request: AIRequest) -> AIResponse:
        client = self._get_client()
        params = self._build_params(request)
        started = time.perf_counter()
        try:
            message = client.messages.create(**params)
        except AIError:
            raise
        except Exception as exc:
            raise self._map_error(exc) from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        if getattr(message, "stop_reason", None) == "refusal":
            raise AIProviderError("The model declined to answer this request")
        text = "".join(
            block.text
            for block in getattr(message, "content", [])
            if getattr(block, "type", None) == "text"
        )
        usage = getattr(message, "usage", None)
        input_tokens = (
            (getattr(usage, "input_tokens", 0) or 0)
            + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
            + (getattr(usage, "cache_read_input_tokens", 0) or 0)
        )
        return AIResponse(
            text=text,
            provider=self.name,
            model=getattr(message, "model", None) or self.model,
            usage=AIUsageInfo(
                input_tokens=input_tokens,
                output_tokens=getattr(usage, "output_tokens", 0) or 0,
            ),
            latency_ms=latency_ms,
        )

    @staticmethod
    def _map_error(exc: Exception) -> AIError:
        """Translate SDK errors; messages carry the status only (never bodies,
        which could echo prompt content)."""
        sdk = _import_sdk()
        if isinstance(exc, sdk.RateLimitError):
            return AIRateLimited("The AI provider rate limit was hit; try again later")
        if isinstance(exc, sdk.APIConnectionError):  # includes APITimeoutError
            return AIUnavailable("The AI provider could not be reached (timeout or network)")
        if isinstance(exc, sdk.APIStatusError):
            status = int(getattr(exc, "status_code", 0) or 0)
            if status >= 500:
                return AIUnavailable(f"The AI provider is unavailable (HTTP {status})")
            if status == 429:
                return AIRateLimited("The AI provider rate limit was hit; try again later")
            return AIProviderError(f"The AI provider rejected the request (HTTP {status})")
        if isinstance(exc, sdk.APIError):
            return AIProviderError("The AI provider returned an error")
        return AIProviderError("Unexpected error calling the AI provider")
