#!/usr/bin/env python3
"""Run a token cost audit on an agent configuration.

Usage:
    python audit.py examples/support_agent
"""

import json
import sys
from pathlib import Path

from token_audit.counter import count_tokens, count_tools_tokens
from token_audit.cost_model import Scenario
from token_audit.optimizers import analyze
from token_audit.report import make_chart, make_report


def load_config(agent_dir: Path, variant: str) -> tuple[int, int]:
    sys_tok = count_tokens((agent_dir / variant / "system_prompt.md").read_text())
    tools_tok = count_tools_tokens(json.loads((agent_dir / variant / "tools.json").read_text()))
    return sys_tok, tools_tok


def main(agent_dir: str) -> None:
    agent = Path(agent_dir)
    profile = json.loads((agent / "traffic_profile.json").read_text())

    sys_b, tools_b = load_config(agent, "baseline")
    sys_o, tools_o = load_config(agent, "optimized")

    baseline = Scenario(
        name="baseline",
        static_prefix_tokens=sys_b + tools_b,
        history_tokens=profile["avg_conversation_history_tokens"],
        user_msg_tokens=profile["avg_user_message_tokens"],
        output_tokens=profile["avg_output_tokens_baseline"],
        requests_per_month=profile["requests_per_month"],
        routing_mix={profile["baseline_model"]: 1.0},
        cache_hit_rate=0.0,
    )

    routing = {v["model"]: v["share"] for v in profile["routing"]["mix"].values()}
    optimized = Scenario(
        name="optimized",
        static_prefix_tokens=sys_o + tools_o,
        history_tokens=profile["avg_conversation_history_tokens"],
        user_msg_tokens=profile["avg_user_message_tokens"],
        output_tokens=profile["avg_output_tokens_optimized"],
        requests_per_month=profile["requests_per_month"],
        routing_mix=routing,
        cache_hit_rate=profile["cache"]["hit_rate"],
    )

    findings = analyze(sys_b, sys_o, tools_b, tools_o, profile)

    out = Path("output")
    out.mkdir(exist_ok=True)
    make_report(baseline, optimized, findings, out / "audit_report.md")
    make_chart(baseline, optimized, out / "cost_chart.png")

    b, o = baseline.monthly_cost(), optimized.monthly_cost()
    print(f"Static prefix: {baseline.static_prefix_tokens:,} -> {optimized.static_prefix_tokens:,} tokens")
    print(f"Monthly cost:  ${b['total']:,.0f} -> ${o['total']:,.0f} "
          f"({(1 - o['total'] / b['total']) * 100:.0f}% reduction)")
    print(f"Annual saving: ${(b['total'] - o['total']) * 12:,.0f}")
    print(f"Report: {out / 'audit_report.md'}  Chart: {out / 'cost_chart.png'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "examples/support_agent")
