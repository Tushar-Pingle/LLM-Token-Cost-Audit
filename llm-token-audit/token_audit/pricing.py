"""Model pricing table. Rates verified against Anthropic's public pricing, July 2026.

All prices are USD per million tokens (MTok), standard API rates.
Cache multipliers per Anthropic prompt caching docs:
  - cache write (5-min TTL): 1.25x base input
  - cache read (hit):        0.10x base input
"""

from dataclasses import dataclass

CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10


@dataclass(frozen=True)
class ModelPrice:
    model_id: str
    input_per_mtok: float
    output_per_mtok: float

    @property
    def cache_write_per_mtok(self) -> float:
        return self.input_per_mtok * CACHE_WRITE_MULTIPLIER

    @property
    def cache_read_per_mtok(self) -> float:
        return self.input_per_mtok * CACHE_READ_MULTIPLIER


PRICING: dict[str, ModelPrice] = {
    "claude-haiku-4-5": ModelPrice("claude-haiku-4-5", 1.00, 5.00),
    "claude-sonnet-4-6": ModelPrice("claude-sonnet-4-6", 3.00, 15.00),
    "claude-opus-4-8": ModelPrice("claude-opus-4-8", 5.00, 25.00),
}


def get_price(model_id: str) -> ModelPrice:
    try:
        return PRICING[model_id]
    except KeyError:
        raise ValueError(
            f"Unknown model '{model_id}'. Known: {', '.join(PRICING)}"
        ) from None
