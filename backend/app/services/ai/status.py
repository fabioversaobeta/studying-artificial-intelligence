"""Read-only status of the AI layer, for the internal ``GET /ai/status`` probe."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories import ai_usage_repository
from app.repositories.ai_usage_repository import UsageTotals
from app.services.ai.service import AIService


def _totals(t: UsageTotals) -> dict[str, object]:
    return {
        "calls": t.calls,
        "input_tokens": t.input_tokens,
        "output_tokens": t.output_tokens,
        "estimated_cost_usd": t.estimated_cost_usd,
    }


def get_status(db: Session, service: AIService, user_id: uuid.UUID) -> dict[str, object]:
    """Configured provider/model and the user's usage. Never includes the API key."""
    midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    limit = service.settings.ai_daily_token_limit
    return {
        "provider": service.provider.name,
        "model": service.provider.model,
        "configured": service.configured,
        "daily_token_limit": limit if limit > 0 else None,
        "usage_today": _totals(ai_usage_repository.totals(db, user_id=user_id, since=midnight)),
        "usage_total": _totals(ai_usage_repository.totals(db, user_id=user_id)),
    }
