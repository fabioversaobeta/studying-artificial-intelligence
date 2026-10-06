from decimal import Decimal

from pydantic import BaseModel


class AIUsageTotalsRead(BaseModel):
    calls: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal | None


class AIStatusRead(BaseModel):
    provider: str
    model: str
    configured: bool
    daily_token_limit: int | None
    usage_today: AIUsageTotalsRead
    usage_total: AIUsageTotalsRead
