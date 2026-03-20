"""Orchestration pipeline for aai2.

Runs the full staged analysis:
  Stage 1 (01_scout)     – FileSummarizer   : chunk & summarize repo files
  Stage 2 (02_aggregate) – ContextManager   : reduce summaries to fit architect window
  Stage 3 (03_draft)     – ArchitectAgent   : produce initial Mermaid diagram
  Stage 4 (04_critique)  – CritiqueAgent    : critique the diagram
  Stage 5 (05_refined)   – ArchitectAgent   : revise diagram using critic feedback
  Stage 6 (06_visual)    – renderer         : (optional) render PNGs
"""

from __future__ import annotations
import time
import re
from pathlib import Path
from lib.agents import STAGES, ArchitectAgent, ContextManager, CritiqueAgent, FileSummarizer
from lib.llm import get_model
from lib.mermaid_renderer import render_mermaid_file


def _log(message: str, start: float, verbose: bool) -> None:
    if not verbose:
        return
    elapsed = time.perf_counter() - start
    print(f"[{elapsed:7.2f}s] {message}")


def run_pipeline(
    repo_path: str | Path,
    out_dir: str | Path = "output_analysis",
    arch_md_path: str | Path | None = None,
    max_chars_per_chunk: int = 50_000,
    architect_threshold: int = 20_000,
    critic_rounds: int = 1,
    verbose: bool = True,
) -> Path:
    """Run the full aai2 pipeline and return the output directory path.

    Parameters
    ----------
    repo_path:
        Path to the repository to analyse.
    out_dir:
        Root output directory.  Stage sub-directories are created automatically.
    arch_md_path:
        Optional path to an external reference architecture ``.md`` file.
    max_chars_per_chunk:
        Maximum characters per file chunk sent to the FileSummarizer LLM.
    architect_threshold:
        Maximum total characters the ContextManager will pass to the Architect.
    critic_rounds:
        Number of critique → revision cycles to run (default 1).
    verbose:
        Print progress messages.

    Returns
    -------
    Path
        The resolved output directory.
    """
    started = time.perf_counter()
    output_dir = Path(out_dir)

    # Ensure all stage directories exist up front
    for stage in STAGES:
        (output_dir / stage).mkdir(parents=True, exist_ok=True)

    _log(f"Starting pipeline | repo={repo_path}", started, verbose)

    llm = get_model()
    _log("LLM initialised", started, verbose)

    # ------------------------------------------------------------------
    # Stage 1 – Scout / FileSummarizer
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Stage 2 – Aggregate / ContextManager
    # ------------------------------------------------------------------
    _log("Stage 2 - ContextManager", started, verbose)
    aggregator = ContextManager(
        output_dir=output_dir,
        architect_threshold=architect_threshold,
    )
    raw_summaries = aggregator.collect_files()
    summary_texts = [f["content"] for f in raw_summaries]
    aggregator.reduce(summary_texts, llm)

    # ------------------------------------------------------------------
    # Stage 3 – Draft / ArchitectAgent
    # ------------------------------------------------------------------
    _log("Stage 3 – ArchitectAgent (draft)", started, verbose)
    architect = ArchitectAgent(
        output_dir=output_dir,
        arch_md_path=arch_md_path,
    )
    diagram = architect.draft(llm)
    if diagram is None:
        raise RuntimeError("ArchitectAgent draft returned no output.")

    # ------------------------------------------------------------------
    # Stages 4 & 5 – Critique → Revise (repeated critic_rounds times)
    # ------------------------------------------------------------------
    for round_idx in range(1, critic_rounds + 1):
        _log(f"Stage 4 – CritiqueAgent (round {round_idx}/{critic_rounds})", started, verbose)
        critic = CritiqueAgent(
            output_dir=output_dir,
            arch_md_path=arch_md_path,
        )
        critique = critic.critique(llm)
        if critique is None:
            _log("  CritiqueAgent returned no output – skipping revision.", started, verbose)
            break

        _log(f"Stage 5 – ArchitectAgent (revision round {round_idx}/{critic_rounds})", started, verbose)
        diagram = architect.revise(llm, arch_md_path=arch_md_path)
        if diagram is None:
            _log("  ArchitectAgent revision returned no output.", started, verbose)
            break

    # ------------------------------------------------------------------
    # Stage 6 – Visual / Renderer
    # ------------------------------------------------------------------
    _log("Stage 6 – Rendering Mermaid diagrams to PNG", started, verbose)
    visual_dir = output_dir / STAGES[5]  # 06_visual
    for stage_idx, label in [(2, "draft"), (4, "refined")]:
        md_src = output_dir / STAGES[stage_idx] / "mermaid.md"
        if md_src.exists():
            md_content = md_src.read_text(encoding="utf-8")
            match = re.search(r"```mermaid\s*(.*?)```", md_content, re.DOTALL)
            mermaid_src = match.group(1).strip() if match else md_content.strip()
            mmd_path = visual_dir / f"mermaid_{label}.mmd"
            mmd_path.write_text(mermaid_src, encoding="utf-8")
            try:
                rendered = render_mermaid_file(
                    mermaid_file=mmd_path,
                    docs_dir=visual_dir,
                    output_stem=f"mermaid_{label}",
                )
                _log(f"  Rendered {label}: {[str(p) for p in rendered]}", started, verbose)
            except RuntimeError as exc:
                _log(f"  Skipping {label} render: {exc}", started, verbose)
        else:
            _log(f"  Not found: {md_src}", started, verbose)

    total = time.perf_counter() - started
    _log(f"Pipeline complete in {total:.1f}s | output → {output_dir.resolve()}", started, verbose)
    return output_dir.resolve()
