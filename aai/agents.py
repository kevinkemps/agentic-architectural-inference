"""Agent implementations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openai import OpenAI

from .llm import complete_json
from .prompts import (
    ARCHITECT_PROMPT,
    ARCHITECT_REVISION_PROMPT,
    CONTEXT_MANAGER_PROMPT,
    CRITIC_PROMPT,
    FILE_SUMMARIZER_PROMPT,
)
from .repo_reader import SourceFile


@dataclass
class RunArtifacts:
    file_summaries: list[dict[str, Any]]
    partitions: list[dict[str, Any]]
    architecture: dict[str, Any]
    critic_reports: list[dict[str, Any]]
    run_stats: dict[str, Any]


def summarize_file(
    client: "OpenAI",
    model: str,
    repo_readme: str,
    source_file: SourceFile,
    verbose: bool = False,
) -> dict[str, Any]:
    payload = {
        "repo_readme": repo_readme[:6000],
        "file_path": source_file.path,
        "file_content": source_file.content,
    }
    return complete_json(
        client=client,
        model=model,
        system_prompt=FILE_SUMMARIZER_PROMPT,
        user_prompt=json.dumps(payload, ensure_ascii=True),
        log_label=f"file_summarizer:{source_file.path}",
        verbose=verbose,
    )


def partition_summaries(
    client: "OpenAI",
    model: str,
    repo_readme: str,
    file_summaries: list[dict[str, Any]],
    verbose: bool = False,
) -> list[dict[str, Any]]:
    payload = {
        "repo_readme": repo_readme[:6000],
        "file_summaries": file_summaries,
    }
    result = complete_json(
        client=client,
        model=model,
        system_prompt=CONTEXT_MANAGER_PROMPT,
        user_prompt=json.dumps(payload, ensure_ascii=True),
        log_label="context_manager",
        verbose=verbose,
    )
    return result.get("partitions", [])


def propose_architecture(
    client: "OpenAI",
    model: str,
    repo_readme: str,
    partitions: list[dict[str, Any]],
    file_summaries: list[dict[str, Any]],
    verbose: bool = False,
) -> dict[str, Any]:
    payload = {
        "repo_readme": repo_readme[:6000],
        "partitions": partitions,
        "file_summaries": file_summaries,
    }
    return complete_json(
        client=client,
        model=model,
        system_prompt=ARCHITECT_PROMPT,
        user_prompt=json.dumps(payload, ensure_ascii=True),
        log_label="architect_initial",
        verbose=verbose,
    )


def critic_review(
    client: "OpenAI",
    model: str,
    architecture: dict[str, Any],
    partitions: list[dict[str, Any]],
    file_summaries: list[dict[str, Any]],
    round_idx: int,
    verbose: bool = False,
) -> dict[str, Any]:
    payload = {
        "architecture": architecture,
        "partitions": partitions,
        "file_summaries": file_summaries,
    }
    return complete_json(
        client=client,
        model=model,
        system_prompt=CRITIC_PROMPT,
        user_prompt=json.dumps(payload, ensure_ascii=True),
        log_label=f"critic_round_{round_idx}",
        verbose=verbose,
    )


def revise_architecture(
    client: "OpenAI",
    model: str,
    architecture: dict[str, Any],
    critic_feedback: dict[str, Any],
    partitions: list[dict[str, Any]],
    file_summaries: list[dict[str, Any]],
    round_idx: int,
    verbose: bool = False,
) -> dict[str, Any]:
    payload = {
        "architecture": architecture,
        "critic_feedback": critic_feedback,
        "partitions": partitions,
        "file_summaries": file_summaries,
    }
    return complete_json(
        client=client,
        model=model,
        system_prompt=ARCHITECT_REVISION_PROMPT,
        user_prompt=json.dumps(payload, ensure_ascii=True),
        log_label=f"architect_revision_round_{round_idx}",
        verbose=verbose,
    )
