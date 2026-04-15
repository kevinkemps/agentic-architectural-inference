"""Prompt templates for the multi-agent architecture pipeline."""

from __future__ import annotations

from pathlib import Path

# Prompts directory is at the repo root (two levels up from this file)
PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def _load_prompt(filename: str, fallback: str) -> str:
    path = PROMPTS_DIR / filename
    try:
        text = path.read_text(encoding="utf-8").strip()
        return text if text else fallback
    except OSError:
        return fallback


def load_evolved_prompt(version: str) -> str | None:
    """Load an evolved critic prompt by version string.
    
    Args:
        version: Version identifier (e.g., "v1", "v2")
        
    Returns:
        Prompt text if found, None otherwise.
    """
    filename = f"critic-agent-v2-evolved-{version}.md"
    path = PROMPTS_DIR / filename
    try:
        text = path.read_text(encoding="utf-8").strip()
        return text if text else None
    except OSError:
        return None


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

DESIGNER_PROMPT = _load_prompt(
    "designer-agent.md",
    "You are Designer Agent that evolves critique strategies.",
)
