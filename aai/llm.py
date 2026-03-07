"""OpenAI client helpers."""

from __future__ import annotations

import copy
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openai import OpenAI


@dataclass
class LLMStats:
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    total_seconds: float = 0.0


_STATS = LLMStats()


def build_client() -> "OpenAI":
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    from openai import OpenAI

    return OpenAI()


def reset_stats() -> None:
    global _STATS
    _STATS = LLMStats()


def snapshot_stats() -> dict[str, Any]:
    return asdict(copy.deepcopy(_STATS))


def _extract_usage(response: Any) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return (0, 0, 0)

    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    total_tokens = int(
        getattr(usage, "total_tokens", input_tokens + output_tokens)
        or (input_tokens + output_tokens)
    )
    return (input_tokens, output_tokens, total_tokens)


def _parse_json_response(text: str) -> dict[str, Any]:
    candidate = text.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Handle fenced code blocks like ```json ... ```
    fenced_blocks = re.findall(r"```(?:json)?\s*(.*?)```", candidate, flags=re.DOTALL)
    for block in fenced_blocks:
        block = block.strip()
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue

    # Fallback: parse the largest object-like slice.
    left = candidate.find("{")
    right = candidate.rfind("}")
    if left != -1 and right != -1 and right > left:
        maybe = candidate[left : right + 1]
        try:
            return json.loads(maybe)
        except json.JSONDecodeError:
            pass

    raise RuntimeError(f"Model returned non-JSON response:\n{candidate}")


def complete_json(
    client: "OpenAI",
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    log_label: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    start = time.perf_counter()
    response = client.responses.create(
        model=model,
        temperature=temperature,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
    )
    elapsed = time.perf_counter() - start
    input_tokens, output_tokens, total_tokens = _extract_usage(response)

    _STATS.requests += 1
    _STATS.input_tokens += input_tokens
    _STATS.output_tokens += output_tokens
    _STATS.total_tokens += total_tokens
    _STATS.total_seconds += elapsed

    if verbose:
        label = log_label or "llm_call"
        print(
            f"[LLM] {label} | {elapsed:.2f}s | "
            f"in={input_tokens} out={output_tokens} total={total_tokens}"
        )

    text = response.output_text.strip()
    return _parse_json_response(text)
