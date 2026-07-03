# Token Cost Audit Report — Customer Support Agent

**Result: 83% cost reduction. $21,612/mo → $3,585/mo ($216,328/yr saved at 1M requests/month).**

## Per-request input footprint

| | Baseline | Optimized |
|---|---|---|
| Static prefix (system + tools) | 4,784 tok | 1,515 tok |
| Dynamic (history + user msg) | 1,020 tok | 1,020 tok |
| Avg output | 280 tok | 170 tok |

## Monthly cost breakdown (USD)

| Component | Baseline | Optimized | Delta |
|---|---|---|---|
| Static prefix input | $14,352 | $406 | -$13,946 |
| Dynamic input | $3,060 | $1,734 | -$1,326 |
| Output | $4,200 | $1,445 | -$2,755 |
| **Total** | **$21,612** | **$3,585** | **-$18,027 (83%)** |

## Optimization levers applied

### 1. System prompt compression
- Baseline: 1,443 tokens
- Optimized: 384 tokens (-73%)
- Prose policies rewritten as tables and terse rules. No information removed; filler, restatement, and throat-clearing removed. Paid on every request.

### 2. Tool schema trimming
- Baseline: 3,341 tokens
- Optimized: 1,131 tokens (-66%)
- Descriptions reduced to what/when. Policy details (refund limits, return windows) stated once in the system prompt instead of repeated per tool.

### 3. Prompt caching
- Baseline: disabled
- Optimized: enabled, 95% hit rate
- Static prefix (system prompt + tools) marked with cache_control. Cache reads bill at 10% of input rate; misses pay a 1.25x write premium.

### 4. Model routing
- Baseline: 100% Sonnet 4.6
- Optimized: 65% haiku / 35% sonnet
- Simple intents (status, tracking, balance checks) route to Haiku 4.5 at 1/3 the input price and 1/3 the output price. Shares must be validated against real transcripts.

### 5. Output discipline
- Baseline: 280 avg output tokens
- Optimized: 170 avg output tokens (-39%)
- Reply length cap + removal of mandated greetings/restating/sign-offs. Output tokens cost 5x input, making this the highest-leverage prompt-level change.

## Method notes

- Token counts via tiktoken (cl100k_base) as an offline proxy; production audits should use Anthropic's `count_tokens` endpoint for exact per-model counts. Relative deltas are robust to the proxy choice.
- Pricing: standard Anthropic API rates verified July 2026 (Haiku 4.5 $1/$5, Sonnet 4.6 $3/$15 per MTok; cache reads 0.10x, writes 1.25x input).
- Routing shares and cache hit rate are stated assumptions in `traffic_profile.json`; validate against production transcripts before presenting savings as committed.
- Quality guardrail: prompt/schema compression preserved all policy content. Any such change should ship behind an eval suite comparing task success before/after.