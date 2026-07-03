"""Cost model: turns token counts + a traffic profile into monthly dollars.

Per-request input = static prefix (system prompt + tool schemas)
                  + conversation history + user message.

With prompt caching, the static prefix is billed at:
    hit_rate  * cache_read rate  (0.10x input)
  + miss_rate * cache_write rate (1.25x input)
Dynamic tokens (history + user message) are always billed at full input rate.

With model routing, traffic is split across models by share; each slice is
costed independently and summed.
"""

from dataclasses import dataclass, field

from .pricing import get_price


@dataclass
class Scenario:
    """One costed configuration (e.g. 'baseline' or 'optimized')."""

    name: str
    static_prefix_tokens: int          # system prompt + tools, sent every request
    history_tokens: int                # avg conversation history per request
    user_msg_tokens: int               # avg user message per request
    output_tokens: int                 # avg output per request
    requests_per_month: int
    routing_mix: dict[str, float]      # {model_id: traffic_share}, shares sum to 1
    cache_hit_rate: float = 0.0        # 0 disables caching

    def monthly_cost(self) -> dict:
        """Return cost breakdown in USD for one month of traffic."""
        totals = {"static_input": 0.0, "dynamic_input": 0.0, "output": 0.0}
        dynamic_tokens = self.history_tokens + self.user_msg_tokens

        for model_id, share in self.routing_mix.items():
            price = get_price(model_id)
            reqs = self.requests_per_month * share

            # Static prefix: cached vs uncached blend
            if self.cache_hit_rate > 0:
                per_tok = (
                    self.cache_hit_rate * price.cache_read_per_mtok
                    + (1 - self.cache_hit_rate) * price.cache_write_per_mtok
                )
            else:
                per_tok = price.input_per_mtok
            totals["static_input"] += reqs * self.static_prefix_tokens * per_tok / 1e6

            totals["dynamic_input"] += reqs * dynamic_tokens * price.input_per_mtok / 1e6
            totals["output"] += reqs * self.output_tokens * price.output_per_mtok / 1e6

        totals["total"] = sum(totals.values())
        totals["annual"] = totals["total"] * 12
        return totals

    def tokens_per_request(self) -> int:
        return self.static_prefix_tokens + self.history_tokens + self.user_msg_tokens
