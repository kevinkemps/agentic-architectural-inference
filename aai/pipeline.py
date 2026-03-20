"""LangGraph-based orchestration pipeline for aai2.

Stages
------
  scout      – FileSummarizer   : chunk & summarise repo files
  aggregate  – ContextManager   : reduce summaries to fit architect window
  draft      – ArchitectAgent   : produce initial Mermaid diagram
  critique   – CritiqueAgent    : critique the diagram
  revise     – ArchitectAgent   : revise diagram using critic feedback
  render     – renderer         : (optional) render PNGs

The critique → revise cycle is handled by a LangGraph conditional edge that
loops back until `critic_rounds` iterations are exhausted or an agent returns
no output.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from lib.agents import STAGES, ArchitectAgent, ContextManager, CritiqueAgent, FileSummarizer
from lib.chunking import LangChainChunker
from lib.llm import get_model
from lib.mermaid_renderer import render_mermaid_file

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    """Immutable run-time configuration passed via LangGraph's configurable slot."""

    repo_path: Path
    out_dir: Path = field(default_factory=lambda: Path("output_analysis"))
    arch_md_path: Path | None = None
    max_chars_per_chunk: int = 50_000
    chunk_overlap_chars: int = 500
    architect_threshold: int = 20_000
    critic_rounds: int = 1


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class PipelineState(TypedDict):
    """Mutable state threaded through every node."""

    # Runtime
    config: PipelineConfig
    llm: Any                        # language model instance
    started_at: float               # perf_counter reference

    # Agent handles (created once, reused across nodes)
    scout: FileSummarizer | None
    aggregator: ContextManager | None
    architect: ArchitectAgent | None
    critic: CritiqueAgent | None

    # Data produced by each stage
    files: list[Any]
    chunks: list[Any]
    diagram: str | None
    critique: str | None

    # Loop counter
    rounds_completed: int

    # Accumulated non-fatal warnings / errors
    errors: list[str]


def _initial_state(config: PipelineConfig) -> PipelineState:
    return PipelineState(
        config=config,
        llm=None,
        started_at=time.perf_counter(),
        scout=None,
        aggregator=None,
        architect=None,
        critic=None,
        files=[],
        chunks=[],
        diagram=None,
        critique=None,
        rounds_completed=0,
        errors=[],
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def node_init(state: PipelineState) -> PipelineState:
    """Initialise the LLM and create all stage output directories."""
    cfg = state["config"]

    for stage in STAGES:
        (cfg.out_dir / stage).mkdir(parents=True, exist_ok=True)

    llm = get_model()
    logger.info("LLM initialised")

    return {
        **state,
        "llm": llm,
    }


def node_scout(state: PipelineState) -> PipelineState:
    """Stage 1 – FileSummarizer: collect & chunk repo files, then summarise."""
    cfg = state["config"]
    logger.info("Stage 1 – FileSummarizer | repo=%s", cfg.repo_path)

    scout = FileSummarizer(
        repo_path=cfg.repo_path,
        output_dir=cfg.out_dir,
    )
    chunker = LangChainChunker(
        max_chunk_chars=cfg.max_chars_per_chunk,
        chunk_overlap_chars=cfg.chunk_overlap_chars,
    )

    files = scout.collect_files()
    if not files:
        raise RuntimeError(f"No source files found in {cfg.repo_path}")
    logger.info("  collected %d file(s)", len(files))

    chunks = chunker.chunk_files(files)
    logger.info("  created %d chunk(s)", len(chunks))

    scout.process_all(chunks, state["llm"])

    return {**state, "scout": scout, "files": files, "chunks": chunks}


def node_aggregate(state: PipelineState) -> PipelineState:
    """Stage 2 – ContextManager: reduce summaries to fit the architect token window."""
    cfg = state["config"]
    logger.info("Stage 2 – ContextManager")

    aggregator = ContextManager(
        output_dir=cfg.out_dir,
        architect_threshold=cfg.architect_threshold,
    )
    raw_summaries = aggregator.collect_files()
    summary_texts = [f["content"] for f in raw_summaries]
    aggregator.reduce(summary_texts, state["llm"])

    return {**state, "aggregator": aggregator}


def node_draft(state: PipelineState) -> PipelineState:
    """Stage 3 – ArchitectAgent: produce the initial Mermaid diagram."""
    cfg = state["config"]
    logger.info("Stage 3 – ArchitectAgent (draft)")

    architect = ArchitectAgent(
        output_dir=cfg.out_dir,
        arch_md_path=cfg.arch_md_path,
    )
    diagram = architect.draft(state["llm"])

    if diagram is None:
        raise RuntimeError("ArchitectAgent draft returned no output.")

    return {**state, "architect": architect, "diagram": diagram}


def node_critique(state: PipelineState) -> PipelineState:
    """Stage 4 – CritiqueAgent: critique the current diagram."""
    cfg = state["config"]
    round_num = state["rounds_completed"] + 1
    logger.info("Stage 4 – CritiqueAgent (round %d/%d)", round_num, cfg.critic_rounds)

    # Reuse existing critic instance if available
    critic = state["critic"] or CritiqueAgent(
        output_dir=cfg.out_dir,
        arch_md_path=cfg.arch_md_path,
    )
    critique = critic.critique(state["llm"])

    if critique is None:
        logger.warning("  CritiqueAgent returned no output – will skip revision.")

    return {**state, "critic": critic, "critique": critique}


def node_revise(state: PipelineState) -> PipelineState:
    """Stage 5 – ArchitectAgent: revise diagram using critic feedback."""
    cfg = state["config"]
    round_num = state["rounds_completed"] + 1
    logger.info("Stage 5 – ArchitectAgent (revision round %d/%d)", round_num, cfg.critic_rounds)

    diagram = state["architect"].revise(state["llm"], arch_md_path=cfg.arch_md_path)

    if diagram is None:
        logger.warning("  ArchitectAgent revision returned no output.")
        errors = state["errors"] + ["Revision round %d produced no output." % round_num]
        return {**state, "rounds_completed": round_num, "errors": errors}

    return {**state, "diagram": diagram, "rounds_completed": round_num}


def node_render(state: PipelineState) -> PipelineState:
    """Stage 6 – Renderer: convert Mermaid markdown files to PNG."""
    cfg = state["config"]
    logger.info("Stage 6 – Rendering Mermaid diagrams to PNG")

    visual_dir = cfg.out_dir / STAGES[5]  # 06_visual
    errors = list(state["errors"])

    render_targets = [
        (STAGES[2], "draft"),    # 03_draft
        (STAGES[4], "refined"),  # 05_refined
    ]

    for stage_dir, label in render_targets:
        md_src = cfg.out_dir / stage_dir / "mermaid.md"
        if not md_src.exists():
            logger.info("  Not found: %s", md_src)
            continue

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
            logger.info("  Rendered %s: %s", label, [str(p) for p in rendered])
        except RuntimeError as exc:
            logger.warning("  Skipping %s render: %s", label, exc)
            errors.append(f"Render skipped for {label}: {exc}")

    return {**state, "errors": errors}


# ---------------------------------------------------------------------------
# Conditional edge: should we run another critique → revise cycle?
# ---------------------------------------------------------------------------

def should_loop(state: PipelineState) -> str:
    """Return 'critique' to loop again, or 'render' to proceed to rendering."""
    cfg = state["config"]

    # Stop if the last critique produced nothing
    if state["critique"] is None:
        logger.info("  No critique output – exiting loop.")
        return "render"

    # Stop if we've hit the requested number of rounds
    if state["rounds_completed"] >= cfg.critic_rounds:
        return "render"

    return "critique"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("init", node_init)
    graph.add_node("scout", node_scout)
    graph.add_node("aggregate", node_aggregate)
    graph.add_node("draft", node_draft)
    graph.add_node("critique", node_critique)
    graph.add_node("revise", node_revise)
    graph.add_node("render", node_render)

    # Linear path up to the first critique
    graph.add_edge(START, "init")
    graph.add_edge("init", "scout")
    graph.add_edge("scout", "aggregate")
    graph.add_edge("aggregate", "draft")
    graph.add_edge("draft", "critique")

    # Critique always feeds into revise
    graph.add_edge("critique", "revise")

    # After revision: loop back to critique OR proceed to render
    graph.add_conditional_edges("revise", should_loop, {"critique": "critique", "render": "render"})

    graph.add_edge("render", END)

    return graph


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    repo_path: str | Path,
    out_dir: str | Path = "output_analysis",
    arch_md_path: str | Path | None = None,
    max_chars_per_chunk: int = 50_000,
    chunk_overlap_chars: int = 500,
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
    chunk_overlap_chars:
        Character overlap passed to the LangChain text splitter for large files.
    architect_threshold:
        Maximum estimated prompt tokens the ContextManager will pass to the Architect.
    critic_rounds:
        Number of critique → revision cycles to run (default 1).
    verbose:
        If True, configure logging at INFO level.

    Returns
    -------
    Path
        The resolved output directory.
    """
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(relativeCreated)7.0fms] %(message)s",
        )

    config = PipelineConfig(
        repo_path=Path(repo_path),
        out_dir=Path(out_dir),
        arch_md_path=Path(arch_md_path) if arch_md_path else None,
        max_chars_per_chunk=max_chars_per_chunk,
        chunk_overlap_chars=chunk_overlap_chars,
        architect_threshold=architect_threshold,
        critic_rounds=critic_rounds,
    )

    graph = build_graph().compile()
    final_state: PipelineState = graph.invoke(_initial_state(config))

    elapsed = time.perf_counter() - final_state["started_at"]
    logger.info("Pipeline complete in %.1fs | output → %s", elapsed, config.out_dir.resolve())

    if final_state["errors"]:
        logger.warning("Non-fatal errors:\n  %s", "\n  ".join(final_state["errors"]))

    return config.out_dir.resolve()
