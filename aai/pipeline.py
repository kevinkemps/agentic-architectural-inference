"""Orchestration pipeline for architecture inference runs."""

from __future__ import annotations

import re
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__:
    from .evaluation.service import build_repo_digest
    from .lib.agents import (
        STAGES,
        ArchitectAgent,
        ContextManager,
        CritiqueAgent,
        FileSummarizer,
        SingleShotArchitectAgent,
    )
    from .lib.llm import get_model
    from .lib.mermaid_renderer import render_mermaid_file
else:  # pragma: no cover - supports running from inside aai/
    from evaluation.service import build_repo_digest  # type: ignore[no-redef]
    from lib.agents import (  # type: ignore[no-redef]
        STAGES,
        ArchitectAgent,
        ContextManager,
        CritiqueAgent,
        FileSummarizer,
        SingleShotArchitectAgent,
    )
    from lib.llm import get_model  # type: ignore[no-redef]
    from lib.mermaid_renderer import render_mermaid_file  # type: ignore[no-redef]


@dataclass
class TokenStats:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class StageRunStats:
    stage: str
    duration_seconds: float
    tokens: TokenStats

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["duration_seconds"] = round(self.duration_seconds, 3)
        return payload


@dataclass
class PipelineRunResult:
    output_dir: Path
    mode: str
    used_critic: bool
    draft_diagram_path: Path | None
    refined_diagram_path: Path | None
    selected_diagram_path: Path | None
    selected_mermaid_path: Path | None
    rendered_assets: dict[str, list[str]]
    stage_stats: list[StageRunStats]
    total_duration_seconds: float
    total_tokens: TokenStats

    def to_dict(self) -> dict:
        return {
            "output_dir": str(self.output_dir),
            "mode": self.mode,
            "used_critic": self.used_critic,
            "draft_diagram_path": str(self.draft_diagram_path) if self.draft_diagram_path else None,
            "refined_diagram_path": str(self.refined_diagram_path) if self.refined_diagram_path else None,
            "selected_diagram_path": str(self.selected_diagram_path) if self.selected_diagram_path else None,
            "selected_mermaid_path": str(self.selected_mermaid_path) if self.selected_mermaid_path else None,
            "rendered_assets": self.rendered_assets,
            "stage_stats": [stage.to_dict() for stage in self.stage_stats],
            "total_duration_seconds": round(self.total_duration_seconds, 3),
            "total_tokens": asdict(self.total_tokens),
        }


def _log(message: str, start: float, verbose: bool) -> None:
    if not verbose:
        return
    elapsed = time.perf_counter() - start
    print(f"[{elapsed:7.2f}s] {message}")


def _clean_output_directories(output_dir: Path) -> None:
    for stage in STAGES:
        stage_dir = output_dir / stage
        if stage_dir.exists():
            shutil.rmtree(stage_dir)
        stage_dir.mkdir(parents=True, exist_ok=True)


def _token_totals(usages: list[dict | None]) -> TokenStats:
    totals = TokenStats()
    for usage in usages:
        if not usage:
            continue
        totals.input_tokens += int(usage.get("input_tokens", 0) or 0)
        totals.output_tokens += int(usage.get("output_tokens", 0) or 0)
        totals.total_tokens += int(usage.get("total_tokens", 0) or 0)
    return totals


def _track_stage(stage_stats: list[StageRunStats], name: str, started_at: float, token_use: list[dict | None]) -> None:
    stage_stats.append(
        StageRunStats(
            stage=name,
            duration_seconds=time.perf_counter() - started_at,
            tokens=_token_totals(token_use),
        )
    )


def _render_outputs(output_dir: Path, started: float, verbose: bool) -> tuple[dict[str, list[str]], Path | None, Path | None]:
    _log("Stage 6 – Rendering Mermaid diagrams to PNG", started, verbose)
    visual_dir = output_dir / STAGES[5]
    rendered_assets: dict[str, list[str]] = {}
    selected_diagram_path: Path | None = None
    selected_mermaid_path: Path | None = None

    for stage_idx, label in [(2, "draft"), (4, "refined")]:
        md_src = output_dir / STAGES[stage_idx] / "mermaid.md"
        if not md_src.exists():
            continue

        md_content = md_src.read_text(encoding="utf-8")
        match = re.search(r"```mermaid\s*(.*?)```", md_content, re.DOTALL)
        mermaid_src = match.group(1).strip() if match else md_content.strip()
        mmd_path = visual_dir / f"mermaid_{label}.mmd"
        mmd_path.write_text(mermaid_src, encoding="utf-8")
        rendered_assets[label] = [str(mmd_path)]

        try:
            rendered = render_mermaid_file(
                mermaid_file=mmd_path,
                docs_dir=visual_dir,
                output_stem=f"mermaid_{label}",
            )
            rendered_assets[label].extend(str(path) for path in rendered)
            _log(f"  Rendered {label}: {[str(p) for p in rendered]}", started, verbose)
        except RuntimeError as exc:
            _log(f"  Skipping {label} render: {exc}", started, verbose)

        selected_diagram_path = md_src
        selected_mermaid_path = mmd_path

    return rendered_assets, selected_diagram_path, selected_mermaid_path


def run_pipeline(
    repo_path: str | Path,
    out_dir: str | Path = "output_analysis",
    arch_md_path: str | Path | None = None,
    max_chars_per_chunk: int = 50_000,
    architect_threshold: int = 20_000,
    critic_rounds: int = 1,
    verbose: bool = True,
    eval_questions_path: str | Path | None = None,
    enable_designer: bool = False,
    mode: str = "multi_agent",
) -> Path:
    del eval_questions_path, enable_designer
    return run_pipeline_with_details(
        repo_path=repo_path,
        out_dir=out_dir,
        arch_md_path=arch_md_path,
        max_chars_per_chunk=max_chars_per_chunk,
        architect_threshold=architect_threshold,
        critic_rounds=critic_rounds,
        verbose=verbose,
        mode=mode,
    ).output_dir


def run_pipeline_with_details(
    repo_path: str | Path,
    out_dir: str | Path = "output_analysis",
    arch_md_path: str | Path | None = None,
    max_chars_per_chunk: int = 50_000,
    architect_threshold: int = 20_000,
    critic_rounds: int = 1,
    verbose: bool = True,
    mode: str = "multi_agent",
) -> PipelineRunResult:
    started = time.perf_counter()
    output_dir = Path(out_dir)
    used_critic = mode == "multi_agent" and critic_rounds > 0
    stage_stats: list[StageRunStats] = []

    _clean_output_directories(output_dir)
    _log(f"Starting pipeline | repo={repo_path} | mode={mode}", started, verbose)

    llm = get_model()
    _log("LLM initialised", started, verbose)

    draft_diagram_path: Path | None = None
    refined_diagram_path: Path | None = None

    if mode == "single_prompt":
        stage_started = time.perf_counter()
        _log("Stage 3 – SingleShotArchitectAgent", started, verbose)
        repo_digest = build_repo_digest(repo_path)
        architect = SingleShotArchitectAgent(output_dir=output_dir)
        architect.draft_from_digest(llm, repo_digest)
        _track_stage(stage_stats, "03_draft_single_prompt", stage_started, architect.token_use)
        draft_diagram_path = output_dir / STAGES[2] / "mermaid.md"
    else:
        stage_started = time.perf_counter()
        _log("Stage 1 - FileSummarizer", started, verbose)
        scout = FileSummarizer(
            repo_path=repo_path,
            output_dir=output_dir,
            max_chars_per_chunk=max_chars_per_chunk,
        )
        files = scout.collect_files()
        if not files:
            raise RuntimeError(f"No source files found in {repo_path}")
        _log(f"  collected {len(files)} files", started, verbose)
        chunks = scout.create_chunks(files)
        _log(f"  created {len(chunks)} chunk(s)", started, verbose)
        scout.process_all(chunks, llm)
        _track_stage(stage_stats, "01_scout", stage_started, scout.token_use)

        stage_started = time.perf_counter()
        _log("Stage 2 - ContextManager", started, verbose)
        aggregator = ContextManager(
            output_dir=output_dir,
            architect_threshold=architect_threshold,
        )
        raw_summaries = aggregator.collect_files()
        summary_texts = [item["content"] for item in raw_summaries]
        aggregator.reduce(summary_texts, llm)
        _track_stage(stage_stats, "02_aggregate", stage_started, aggregator.token_use)

        architect = ArchitectAgent(
            output_dir=output_dir,
            arch_md_path=arch_md_path,
        )
        stage_started = time.perf_counter()
        _log("Stage 3 – ArchitectAgent (draft)", started, verbose)
        diagram = architect.draft(llm)
        if diagram is None:
            raise RuntimeError("ArchitectAgent draft returned no output.")
        _track_stage(stage_stats, "03_draft", stage_started, architect.token_use)
        draft_diagram_path = output_dir / STAGES[2] / "mermaid.md"

        if used_critic:
            for round_idx in range(1, critic_rounds + 1):
                critic = CritiqueAgent(
                    output_dir=output_dir,
                    arch_md_path=arch_md_path,
                )
                stage_started = time.perf_counter()
                _log(f"Stage 4 – CritiqueAgent (round {round_idx}/{critic_rounds})", started, verbose)
                critique = critic.critique(llm)
                _track_stage(stage_stats, f"04_critique_round_{round_idx}", stage_started, critic.token_use)
                if critique is None:
                    _log("  CritiqueAgent returned no output – skipping revision.", started, verbose)
                    break

                stage_started = time.perf_counter()
                _log(f"Stage 5 – ArchitectAgent (revision round {round_idx}/{critic_rounds})", started, verbose)
                diagram = architect.revise(llm, arch_md_path=arch_md_path)
                round_token_use = architect.token_use[-1:] if architect.token_use else []
                _track_stage(stage_stats, f"05_refined_round_{round_idx}", stage_started, round_token_use)
                if diagram is None:
                    _log("  ArchitectAgent revision returned no output.", started, verbose)
                    break
                refined_diagram_path = output_dir / STAGES[4] / "mermaid.md"

    render_started = time.perf_counter()
    rendered_assets, selected_diagram_path, selected_mermaid_path = _render_outputs(
        output_dir=output_dir,
        started=started,
        verbose=verbose,
    )
    _track_stage(stage_stats, "06_visual", render_started, [])

    total_tokens = TokenStats()
    for stage in stage_stats:
        total_tokens.input_tokens += stage.tokens.input_tokens
        total_tokens.output_tokens += stage.tokens.output_tokens
        total_tokens.total_tokens += stage.tokens.total_tokens

    total = time.perf_counter() - started
    _log(f"Pipeline complete in {total:.1f}s | output → {output_dir.resolve()}", started, verbose)
    return PipelineRunResult(
        output_dir=output_dir.resolve(),
        mode=mode,
        used_critic=used_critic,
        draft_diagram_path=draft_diagram_path,
        refined_diagram_path=refined_diagram_path,
        selected_diagram_path=selected_diagram_path,
        selected_mermaid_path=selected_mermaid_path,
        rendered_assets=rendered_assets,
        stage_stats=stage_stats,
        total_duration_seconds=total,
        total_tokens=total_tokens,
    )
