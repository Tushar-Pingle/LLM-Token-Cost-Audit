"""Token counting with graceful degradation.

Preferred: tiktoken (cl100k_base) as an offline proxy tokenizer.
Fallback:  regex heuristic (each word and punctuation mark ~= 1 token,
           x1.05 correction), used when tiktoken's vocab can't be fetched.

Claude uses its own tokenizer, so both are approximations. For exact,
per-model counts in a production audit, call Anthropic's
/v1/messages/count_tokens endpoint. The before/after deltas this tool
reports are robust to the counter choice because both configurations
are measured with the same counter.
"""

import json
import re
from functools import lru_cache

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


@lru_cache(maxsize=1)
def _encoder():
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        enc.encode("warmup")  # force vocab download now, not on first real call
        return enc
    except Exception:
        return None


def count_tokens(text: str) -> int:
    """Approximate token count for a string."""
    enc = _encoder()
    if enc is not None:
        return len(enc.encode(text))
    return int(len(_TOKEN_RE.findall(text)) * 1.05)


def count_tools_tokens(tools: list[dict]) -> int:
    """Approximate token overhead of tool definitions in the model context.

    Schemas are injected as structured text; compact JSON is a fair proxy.
    """
    return count_tokens(json.dumps(tools, separators=(",", ":")))
