import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_usage import AIUsage


@dataclass(frozen=True)
class UsageTotals:
    calls: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal | None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def add(
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
    estimated_cost_usd: Decimal | None,
    request_id: str | None,
) -> AIUsage:
    row = AIUsage(
        user_id=user_id,
        purpose=purpose,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        status=status,
        estimated_cost_usd=estimated_cost_usd,
        request_id=request_id,
    )
    db.add(row)
    db.flush()
    return row


def totals(
    db: Session, *, user_id: uuid.UUID | None = None, since: datetime | None = None
) -> UsageTotals:
    """Aggregate usage; filtered by user and/or from `since` (inclusive)."""
    stmt = select(
        func.count(AIUsage.id),
        func.coalesce(func.sum(AIUsage.input_tokens), 0),
        func.coalesce(func.sum(AIUsage.output_tokens), 0),
        func.sum(AIUsage.estimated_cost_usd),
    )
    if user_id is not None:
        stmt = stmt.where(AIUsage.user_id == user_id)
    if since is not None:
        stmt = stmt.where(AIUsage.created_at >= since)
    calls, tokens_in, tokens_out, cost = db.execute(stmt).one()
    return UsageTotals(int(calls), int(tokens_in), int(tokens_out), cost)
