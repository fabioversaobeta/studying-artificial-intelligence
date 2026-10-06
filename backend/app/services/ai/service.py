"""``ai_service``: the facade the rest of the app uses to talk to an LLM.

Implements the guardrails of docs/PROPOSAL_TRACK_I.md §2 once:
- provider chosen by Settings (``AI_PROVIDER=fake|claude``), never by callers;
- system prompt always built with the injection preamble and language rule
  (user input must be fenced with ``prompts.delimit`` by the caller);
- ``max_tokens`` capped by ``AI_MAX_OUTPUT_TOKENS``; timeout/retries live in
  the provider client;
- structured output validated against a Pydantic schema, with exactly one
  repair retry; model output is data and is never executed;
- every provider call is measured in ``ai_usage`` (tokens, latency, status,
  estimated cost) -- never the prompt or the answer;
- optional per-user daily token ceiling (``AI_DAILY_TOKEN_LIMIT``; 0 = off);
- logs carry ids, sizes, latency, tokens and model only, plus the request id
  that app.core.logging already puts on every record.
"""

import logging
import re
import time
import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from functools import lru_cache

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import request_id_var
from app.models.ai_usage import AIUsage
from app.repositories import ai_usage_repository
from app.services.ai.base import AIMessage, AIProvider, AIRequest, AIResponse
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.errors import (
    AIError,
    AIInvalidOutput,
    AIProviderError,
    AIRateLimited,
    AIUnavailable,
    AIUsageLimitExceeded,
)
from app.services.ai.fake_provider import FakeProvider
from app.services.ai.pricing import estimate_cost_usd
from app.services.ai.prompts import build_system_prompt, normalize_language

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)

REPAIR_INSTRUCTION = (
    "Your previous reply did not satisfy the required JSON schema ({problems}). "
    "Reply again with only a single JSON object that matches the schema exactly."
)


@dataclass(frozen=True)
class AIResult:
    text: str
    data: BaseModel | None
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


def _status_for(exc: AIError) -> str:
    if isinstance(exc, AIRateLimited):
        return "rate_limited"
    if isinstance(exc, AIUnavailable):
        return "unavailable"
    if isinstance(exc, AIInvalidOutput):
        return "invalid_output"
    return "provider_error"


def _validation_problems(exc: ValidationError) -> str:
    """Field paths and error types only: error inputs could echo model output."""
    items = [f"{'.'.join(str(p) for p in e['loc']) or 'root'}: {e['type']}" for e in exc.errors()]
    return "; ".join(items[:8])


def _parse(schema: type[BaseModel], text: str) -> BaseModel:
    match = _FENCE_RE.match(text)
    return schema.model_validate_json(match.group(1) if match else text)


@lru_cache(maxsize=4)
def _claude_provider(
    api_key: str, model: str, timeout_seconds: float, max_retries: int
) -> ClaudeProvider:
    return ClaudeProvider(
        api_key=api_key, model=model, timeout_seconds=timeout_seconds, max_retries=max_retries
    )


def build_provider(settings: Settings) -> AIProvider:
    """Pick the provider from Settings. Claude without a key degrades to an
    unusable provider that raises ``AIUnavailable`` on use (production boot
    already refuses that combination)."""
    if settings.ai_provider == "claude":
        key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else ""
        if key:
            return _claude_provider(
                key, settings.ai_model, settings.ai_timeout_seconds, settings.ai_max_retries
            )
        return ClaudeProvider(api_key=None, model=settings.ai_model)
    return FakeProvider()


class AIService:
    def __init__(self, provider: AIProvider, settings: Settings) -> None:
        self.provider = provider
        self.settings = settings

    @property
    def configured(self) -> bool:
        """True when the selected provider can serve requests (the fake always can;
        Claude needs an API key)."""
        if self.provider.name == "claude":
            return self.settings.anthropic_api_key is not None
        return True

    # -- public API ---------------------------------------------------------

    def complete(
        self,
        db: Session,
        *,
        purpose: str,
        messages: list[AIMessage],
        system: str = "",
        language: str | None = None,
        output_schema: type[BaseModel] | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        cache_system: bool = False,
        user_id: uuid.UUID | None = None,
    ) -> AIResult:
        if not messages or messages[0].role != "user":
            raise ValueError("messages must start with a user message")
        code = normalize_language(language)
        self._enforce_daily_limit(db, user_id)

        request = AIRequest(
            messages=list(messages),
            system=build_system_prompt(system, code),
            max_tokens=max(1, min(max_tokens, self.settings.ai_max_output_tokens)),
            temperature=temperature,
            output_schema=output_schema,
            language=code,
            purpose=purpose,
            cache_system=cache_system,
        )
        total_in = total_out = 0
        started = time.perf_counter()

        response, _ = self._call(db, request, user_id)
        total_in, total_out = response.usage.input_tokens, response.usage.output_tokens
        data: BaseModel | None = None

        if output_schema is not None:
            try:
                data = _parse(output_schema, response.text)
            except ValidationError as exc:
                repair = replace(
                    request,
                    messages=[
                        *request.messages,
                        AIMessage("assistant", response.text),
                        AIMessage(
                            "user",
                            REPAIR_INSTRUCTION.format(problems=_validation_problems(exc)),
                        ),
                    ],
                )
                response, row = self._call(db, repair, user_id)
                total_in += response.usage.input_tokens
                total_out += response.usage.output_tokens
                try:
                    data = _parse(output_schema, response.text)
                except ValidationError as exc2:
                    row.status = "invalid_output"
                    db.commit()
                    logger.warning(
                        "ai_invalid_output purpose=%s model=%s problems=%s",
                        purpose,
                        response.model,
                        _validation_problems(exc2),
                    )
                    raise AIInvalidOutput(
                        "The AI answer did not match the expected format"
                    ) from None

        return AIResult(
            text=response.text,
            data=data,
            provider=response.provider,
            model=response.model,
            input_tokens=total_in,
            output_tokens=total_out,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    # -- internals ----------------------------------------------------------

    def _call(
        self, db: Session, request: AIRequest, user_id: uuid.UUID | None
    ) -> tuple[AIResponse, AIUsage]:
        started = time.perf_counter()
        try:
            response = self.provider.complete(request)
        except AIError as exc:
            self._record(
                db,
                user_id=user_id,
                purpose=request.purpose,
                provider=self.provider.name,
                model=self.provider.model,
                input_tokens=0,
                output_tokens=0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status=_status_for(exc),
            )
            raise
        except Exception as exc:  # providers must raise AIError; never leak SDK errors
            self._record(
                db,
                user_id=user_id,
                purpose=request.purpose,
                provider=self.provider.name,
                model=self.provider.model,
                input_tokens=0,
                output_tokens=0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="provider_error",
            )
            raise AIProviderError("Unexpected error calling the AI provider") from exc
        row = self._record(
            db,
            user_id=user_id,
            purpose=request.purpose,
            provider=response.provider,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=response.latency_ms,
            status="ok",
        )
        return response, row

    def _record(
        self,
        db: Session,
        *,
        user_id: uuid.UUID | None,
        purpose: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        status: str,
    ) -> AIUsage:
        request_id = request_id_var.get()
        row = ai_usage_repository.add(
            db,
            user_id=user_id,
            purpose=purpose,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            status=status,
            estimated_cost_usd=estimate_cost_usd(model, input_tokens, output_tokens),
            request_id=request_id,
        )
        # Commit now: a later failure in the caller must not erase the record
        # of a call that was made (and billed).
        db.commit()
        logger.info(
            "ai_call purpose=%s provider=%s model=%s status=%s input_tokens=%d "
            "output_tokens=%d latency_ms=%d request_id=%s",
            purpose,
            provider,
            model,
            status,
            input_tokens,
            output_tokens,
            latency_ms,
            request_id,
        )
        return row

    def _enforce_daily_limit(self, db: Session, user_id: uuid.UUID | None) -> None:
        limit = self.settings.ai_daily_token_limit
        if limit <= 0:
            return
        midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        used = ai_usage_repository.totals(db, user_id=user_id, since=midnight).total_tokens
        if used >= limit:
            raise AIUsageLimitExceeded("The daily AI usage limit has been reached")


def get_ai_service(settings: Settings | None = None) -> AIService:
    settings = settings or get_settings()
    return AIService(build_provider(settings), settings)


__all__ = ["AIResult", "AIService", "build_provider", "get_ai_service"]
