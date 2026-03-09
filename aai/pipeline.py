"""Orchestration pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .agents import (
    RunArtifacts,
    critic_review,
    partition_summaries,
    propose_architecture,
    revise_architecture,
    summarize_file,
)
from .llm import build_client, reset_stats, snapshot_stats
from .mermaid_renderer import render_mermaid_file
from .repo_reader import load_readme, load_repo_files


def _log(message: str, start: float, verbose: bool) -> None:
    if not verbose:
        return
    elapsed = time.perf_counter() - start
    print(f"[{elapsed:7.2f}s] {message}")


def _normalize_architecture_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if (
        isinstance(payload, dict)
        and "architecture" in payload
        and isinstance(payload["architecture"], dict)
    ):
        return payload["architecture"]
    return payload


def _sanitize_mermaid_text(text: str) -> str:
    return (
        text.replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )


def _build_mermaid_from_graph(architecture: dict[str, Any]) -> str:
    components = architecture.get("components", [])
    edges = architecture.get("edges", [])
    lines = ["flowchart LR"]

    for component in components:
        component_id = component.get("id")
        if not component_id:
            continue
        label = component.get("label", component_id)
        lines.append(f'  {component_id}["{_sanitize_mermaid_text(str(label))}"]')

    if components and edges:
        lines.append("")

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        label = edge.get("label", "")
        if label:
            lines.append(
                f'  {source} -->|"{_sanitize_mermaid_text(str(label))}"| {target}'
            )
        else:
            lines.append(f"  {source} --> {target}")

    return "\n".join(lines).strip() + "\n"


def run_pipeline(
    repo_path: str,
    model: str,
    max_files: int,
    max_chars_per_file: int,
    critic_rounds: int,
    verbose: bool = True,
) -> RunArtifacts:
    started = time.perf_counter()
    reset_stats()
    _log(
        f"Starting run | repo={repo_path} model={model} critic_rounds={critic_rounds}",
        started,
        verbose,
    )
    client = build_client()
    repo_readme = load_readme(repo_path)
    source_files = load_repo_files(
        repo_path=repo_path,
        max_files=max_files,
        max_chars_per_file=max_chars_per_file,
    )
    if not source_files:
        raise RuntimeError("No source files detected for analysis")
    _log(
        f"Loaded repository context | files={len(source_files)}",
        started,
        verbose,
    )

    file_summaries: list[dict[str, Any]] = []
    for idx, source_file in enumerate(source_files, start=1):
        _log(
            f"File summarizer {idx}/{len(source_files)} | {source_file.path}",
            started,
            verbose,
        )
        summary = summarize_file(
            client=client,
            model=model,
            repo_readme=repo_readme,
            source_file=source_file,
            verbose=verbose,
        )
        file_summaries.append(summary)

    _log("Running context manager partitioning", started, verbose)
    partitions = partition_summaries(
        client=client,
        model=model,
        repo_readme=repo_readme,
        file_summaries=file_summaries,
        verbose=verbose,
    )

    _log("Running architect initial synthesis", started, verbose)
    architecture = propose_architecture(
        client=client,
        model=model,
        repo_readme=repo_readme,
        partitions=partitions,
        file_summaries=file_summaries,
        verbose=verbose,
    )
    architecture = _normalize_architecture_payload(architecture)

    critic_reports: list[dict[str, Any]] = []
    for round_idx in range(1, critic_rounds + 1):
        _log(f"Running critic round {round_idx}/{critic_rounds}", started, verbose)
        report = critic_review(
            client=client,
            model=model,
            architecture=architecture,
            partitions=partitions,
            file_summaries=file_summaries,
            round_idx=round_idx,
            verbose=verbose,
        )
        critic_reports.append(report)
        _log(f"Running architect revision round {round_idx}/{critic_rounds}", started, verbose)
        architecture = revise_architecture(
            client=client,
            model=model,
            architecture=architecture,
            critic_feedback=report,
            partitions=partitions,
            file_summaries=file_summaries,
            round_idx=round_idx,
            verbose=verbose,
        )
        architecture = _normalize_architecture_payload(architecture)

    total_elapsed = time.perf_counter() - started
    llm_stats = snapshot_stats()
    run_stats = {
        "runtime_seconds": round(total_elapsed, 3),
        "files_processed": len(source_files),
        "critic_rounds": critic_rounds,
        "llm": llm_stats,
    }
    _log(
        "Completed run | "
        f"runtime={run_stats['runtime_seconds']}s "
        f"requests={llm_stats['requests']} total_tokens={llm_stats['total_tokens']}",
        started,
        verbose,
    )

    return RunArtifacts(
        file_summaries=file_summaries,
        partitions=partitions,
        architecture=architecture,
        critic_reports=critic_reports,
        run_stats=run_stats,
    )


def write_artifacts(out_dir: str | Path, artifacts: RunArtifacts) -> None:
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    architecture = _normalize_architecture_payload(artifacts.architecture)
    mermaid = architecture.get("mermaid", "").strip()
    if not mermaid:
        mermaid = _build_mermaid_from_graph(architecture)

    (output_path / "architecture.mmd").write_text(
        mermaid if mermaid else "flowchart LR\n",
        encoding="utf-8",
    )

    mermaid_path = output_path / "architecture.mmd"
    mermaid_path.write_text(
        mermaid if mermaid else "flowchart LR\n",
        encoding="utf-8",
    )

    # Render architecture.mmd to docs/diagrams.
    try:
        rendered = render_mermaid_file(
            mermaid_file=mermaid_path,
            docs_dir="docs/diagrams",
            output_stem=f"{output_path.name}_architecture",
        )
        print(f"Rendered docs diagrams: {rendered[0]} and {rendered[1]}")
    except RuntimeError as exc:
        print(f"Skipping Mermaid PNG/SVG render: {exc}")

    (output_path / "architecture.json").write_text(
        json.dumps(architecture, indent=2),
        encoding="utf-8",
    )
    (output_path / "critic_reports.json").write_text(
        json.dumps(artifacts.critic_reports, indent=2),
        encoding="utf-8",
    )
    (output_path / "file_summaries.json").write_text(
        json.dumps(artifacts.file_summaries, indent=2),
        encoding="utf-8",
    )
    (output_path / "partitions.json").write_text(
        json.dumps(artifacts.partitions, indent=2),
        encoding="utf-8",
    )
    (output_path / "run_stats.json").write_text(
        json.dumps(artifacts.run_stats, indent=2),
        encoding="utf-8",
    )

    critic_md_lines = ["# Critic Findings", ""]
    for idx, report in enumerate(artifacts.critic_reports, start=1):
        critic_md_lines.append(f"## Round {idx}")
        critic_md_lines.append(report.get("critic_summary", "No summary"))
        issues = report.get("issues", [])
        if issues:
            critic_md_lines.append("")
            for issue in issues:
                severity = issue.get("severity", "unknown")
                claim = issue.get("claim", "unspecified")
                why = issue.get("why", "no reason provided")
                critic_md_lines.append(f"- [{severity}] {claim}: {why}")
        critic_md_lines.append("")

    (output_path / "critic_report.md").write_text(
        "\n".join(critic_md_lines).strip() + "\n",
        encoding="utf-8",
    )
