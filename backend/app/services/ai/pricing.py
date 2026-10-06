"""Price table used to *estimate* cost in ``ai_usage``.

Data, not logic: USD per million tokens as (input, output), taken from the
public Anthropic price list. Estimates only (no cache discounts, no batch);
the provider's billing console is the source of truth. Unknown models
(including the fake provider) yield ``None`` -- an unknown cost, not zero.
"""

from decimal import Decimal

PRICES_USD_PER_MTOK: dict[str, tuple[Decimal, Decimal]] = {
    "claude-fable-5-1": (Decimal("10"), Decimal("50")),
    "claude-fable-5": (Decimal("10"), Decimal("50")),
    "claude-opus-5-5": (Decimal("4"), Decimal("20")),
    "claude-opus-5": (Decimal("5"), Decimal("25")),
    "claude-opus-4-8": (Decimal("5"), Decimal("25")),
    "claude-sonnet-5-5": (Decimal("2"), Decimal("10")),
    "claude-sonnet-5": (Decimal("2"), Decimal("10")),
    "claude-sonnet-4-6": (Decimal("3"), Decimal("15")),
    "claude-haiku-4-5": (Decimal("1"), Decimal("5")),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> Decimal | None:
    prices = PRICES_USD_PER_MTOK.get(model)
    if prices is None:
        return None
    price_in, price_out = prices
    cost = (price_in * input_tokens + price_out * output_tokens) / Decimal(1_000_000)
    return cost.quantize(Decimal("0.000001"))
