"""Prompt templates for the multi-agent architecture pipeline."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def _load_prompt(filename: str, fallback: str) -> str:
    path = PROMPTS_DIR / filename
    try:
        text = path.read_text(encoding="utf-8").strip()
        return text if text else fallback
    except OSError:
        return fallback


FILE_SUMMARIZER_PROMPT = _load_prompt(
    "file-summarizer.md",
    "You are File Summarizer Agent.",
)

CONTEXT_MANAGER_PROMPT = _load_prompt(
    "context-manager.md",
    "You are Context Manager Agent.",
)

ARCHITECT_PROMPT = _load_prompt(
    "architect.md",
    "You are Architect Agent.",
)

CRITIC_PROMPT = _load_prompt(
    "critic-agent-v2.md",
    "You are Critic Agent.",
)

ARCHITECT_REVISION_PROMPT = _load_prompt(
    "architect-revision.md",
    "You are Architect Agent revising after critic feedback. ",
)
