"""Report generation: markdown audit report + before/after cost chart."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .cost_model import Scenario
from .optimizers import Finding

BRAND_DARK = "#1a1a2e"
BRAND_BASE = "#c44545"
BRAND_OPT = "#2e8b57"


def make_chart(baseline: Scenario, optimized: Scenario, path: str) -> None:
    b, o = baseline.monthly_cost(), optimized.monthly_cost()
    cats = ["static_input", "dynamic_input", "output"]
    labels = ["Static prefix\n(system + tools)", "Dynamic input\n(history + msg)", "Output"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), width_ratios=[3, 2])
    fig.suptitle("LLM Support Agent: Monthly API Cost, Before vs After Optimization",
                 fontsize=14, fontweight="bold", color=BRAND_DARK)

    x = range(len(cats))
    w = 0.38
    ax1.bar([i - w / 2 for i in x], [b[c] for c in cats], w,
            label=f"Baseline (${b['total']:,.0f}/mo)", color=BRAND_BASE)
    ax1.bar([i + w / 2 for i in x], [o[c] for c in cats], w,
            label=f"Optimized (${o['total']:,.0f}/mo)", color=BRAND_OPT)
    ax1.set_xticks(list(x), labels)
    ax1.set_ylabel("USD per month")
    ax1.set_title("Cost by component (1M requests/month)", fontsize=11)
    ax1.legend()
    ax1.spines[["top", "right"]].set_visible(False)
    for i, c in enumerate(cats):
        ax1.text(i - w / 2, b[c], f"${b[c]:,.0f}", ha="center", va="bottom", fontsize=9)
        ax1.text(i + w / 2, o[c], f"${o[c]:,.0f}", ha="center", va="bottom", fontsize=9)

    savings_mo = b["total"] - o["total"]
    savings_pct = savings_mo / b["total"] * 100
    ax2.bar(["Baseline", "Optimized"], [b["annual"], o["annual"]],
            color=[BRAND_BASE, BRAND_OPT], width=0.55)
    ax2.set_ylabel("USD per year")
    ax2.set_title("Annualized", fontsize=11)
    ax2.spines[["top", "right"]].set_visible(False)
    for i, v in enumerate([b["annual"], o["annual"]]):
        ax2.text(i, v, f"${v:,.0f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax2.annotate(f"-{savings_pct:.0f}%\n${savings_mo * 12:,.0f}/yr saved",
                 xy=(0.5, 0.55), xycoords="axes fraction", ha="center",
                 fontsize=13, fontweight="bold", color=BRAND_OPT)

    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()


def make_report(baseline: Scenario, optimized: Scenario,
                findings: list[Finding], path: str) -> None:
    b, o = baseline.monthly_cost(), optimized.monthly_cost()
    savings_mo = b["total"] - o["total"]
    savings_pct = savings_mo / b["total"] * 100

    lines = [
        "# Token Cost Audit Report — Customer Support Agent",
        "",
        f"**Result: {savings_pct:.0f}% cost reduction. "
        f"${b['total']:,.0f}/mo → ${o['total']:,.0f}/mo "
        f"(${savings_mo * 12:,.0f}/yr saved at 1M requests/month).**",
        "",
        "## Per-request input footprint",
        "",
        "| | Baseline | Optimized |",
        "|---|---|---|",
        f"| Static prefix (system + tools) | {baseline.static_prefix_tokens:,} tok | {optimized.static_prefix_tokens:,} tok |",
        f"| Dynamic (history + user msg) | {baseline.history_tokens + baseline.user_msg_tokens:,} tok | {optimized.history_tokens + optimized.user_msg_tokens:,} tok |",
        f"| Avg output | {baseline.output_tokens:,} tok | {optimized.output_tokens:,} tok |",
        "",
        "## Monthly cost breakdown (USD)",
        "",
        "| Component | Baseline | Optimized | Delta |",
        "|---|---|---|---|",
    ]
    for key, label in [("static_input", "Static prefix input"),
                       ("dynamic_input", "Dynamic input"),
                       ("output", "Output")]:
        lines.append(f"| {label} | ${b[key]:,.0f} | ${o[key]:,.0f} | "
                     f"-${b[key] - o[key]:,.0f} |")
    lines += [
        f"| **Total** | **${b['total']:,.0f}** | **${o['total']:,.0f}** | "
        f"**-${savings_mo:,.0f} ({savings_pct:.0f}%)** |",
        "",
        "## Optimization levers applied",
        "",
    ]
    for f in findings:
        lines += [
            f"### {f.lever}",
            f"- Baseline: {f.baseline_value}",
            f"- Optimized: {f.optimized_value}",
            f"- {f.detail}",
            "",
        ]
    lines += [
        "## Method notes",
        "",
        "- Token counts via tiktoken (cl100k_base) as an offline proxy; production audits "
        "should use Anthropic's `count_tokens` endpoint for exact per-model counts. "
        "Relative deltas are robust to the proxy choice.",
        "- Pricing: standard Anthropic API rates verified July 2026 "
        "(Haiku 4.5 $1/$5, Sonnet 4.6 $3/$15 per MTok; cache reads 0.10x, writes 1.25x input).",
        "- Routing shares and cache hit rate are stated assumptions in "
        "`traffic_profile.json`; validate against production transcripts before "
        "presenting savings as committed.",
        "- Quality guardrail: prompt/schema compression preserved all policy content. "
        "Any such change should ship behind an eval suite comparing task success "
        "before/after.",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
