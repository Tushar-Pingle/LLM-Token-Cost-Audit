"""The five optimization levers, expressed as measurable findings.

Each finding compares a slice of the baseline configuration against its
optimized counterpart and reports the token delta. The cost model then
converts the combined configuration change into dollars.

Levers:
  1. System prompt compression   -- rewrite prose to dense reference format
  2. Tool schema trimming        -- what/when descriptions, policy lives in prompt
  3. Prompt caching              -- cache_control on the static prefix
  4. Model routing               -- classify traffic, send simple work to Haiku
  5. Output discipline           -- length caps + no mandated boilerplate
"""

from dataclasses import dataclass


@dataclass
class Finding:
    lever: str
    baseline_value: str
    optimized_value: str
    detail: str


def analyze(
    sys_baseline_tok: int,
    sys_optimized_tok: int,
    tools_baseline_tok: int,
    tools_optimized_tok: int,
    profile: dict,
) -> list[Finding]:
    findings = []

    pct = lambda a, b: f"-{(1 - b / a) * 100:.0f}%"

    findings.append(Finding(
        lever="1. System prompt compression",
        baseline_value=f"{sys_baseline_tok:,} tokens",
        optimized_value=f"{sys_optimized_tok:,} tokens ({pct(sys_baseline_tok, sys_optimized_tok)})",
        detail="Prose policies rewritten as tables and terse rules. No information removed; "
               "filler, restatement, and throat-clearing removed. Paid on every request.",
    ))

    findings.append(Finding(
        lever="2. Tool schema trimming",
        baseline_value=f"{tools_baseline_tok:,} tokens",
        optimized_value=f"{tools_optimized_tok:,} tokens ({pct(tools_baseline_tok, tools_optimized_tok)})",
        detail="Descriptions reduced to what/when. Policy details (refund limits, return windows) "
               "stated once in the system prompt instead of repeated per tool.",
    ))

    cache = profile["cache"]
    findings.append(Finding(
        lever="3. Prompt caching",
        baseline_value="disabled",
        optimized_value=f"enabled, {cache['hit_rate']:.0%} hit rate",
        detail="Static prefix (system prompt + tools) marked with cache_control. "
               "Cache reads bill at 10% of input rate; misses pay a 1.25x write premium.",
    ))

    mix = profile["routing"]["mix"]
    mix_str = " / ".join(f"{v['share']:.0%} {v['model'].split('-')[1]}" for v in mix.values())
    findings.append(Finding(
        lever="4. Model routing",
        baseline_value="100% Sonnet 4.6",
        optimized_value=mix_str,
        detail="Simple intents (status, tracking, balance checks) route to Haiku 4.5 at 1/3 the "
               "input price and 1/3 the output price. Shares must be validated against real transcripts.",
    ))

    out_b = profile["avg_output_tokens_baseline"]
    out_o = profile["avg_output_tokens_optimized"]
    findings.append(Finding(
        lever="5. Output discipline",
        baseline_value=f"{out_b} avg output tokens",
        optimized_value=f"{out_o} avg output tokens ({pct(out_b, out_o)})",
        detail="Reply length cap + removal of mandated greetings/restating/sign-offs. "
               "Output tokens cost 5x input, making this the highest-leverage prompt-level change.",
    ))

    return findings
