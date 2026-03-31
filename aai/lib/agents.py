
"""
Agent classes for the aai2 pipeline.

Hierarchy:
  Agent                  – base class (save_md, collect_files, invoke_llm, …)
  ├── FileSummarizer     – Stage 1: walk repo, chunk files, summarize each chunk
  ├── ContextManager     – Stage 2: reduce scout summaries to fit architect window
  ├── ArchitectAgent     – Stage 3: draft and revise Mermaid diagram
  └── CritiqueAgent      – Stage 4: critique the Mermaid diagram
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

from langchain_core.messages import HumanMessage, SystemMessage

from .prompts import (
    ARCHITECT_PROMPT,
    CONTEXT_MANAGER_PROMPT,
    CRITIC_PROMPT,
    FILE_SUMMARIZER_PROMPT,
)
from .repo_reader import LangChainChunker, TEXT_SUFFIXES

# ---------------------------------------------------------------------------
# Pipeline stage constants
# ---------------------------------------------------------------------------

STAGES = [
    "01_scout",
    "02_aggregate",
    "03_draft",
    "04_critique",
    "05_refined",
    "06_visual",
]


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------

class Agent:
    """Base class for all pipeline agents.

    Provides shared functionality:
      - save_md        : write markdown output to the stage's output directory
      - collect_files  : walk a directory and read all files into dicts
      - calculate_total_size : sum character counts across a list of strings
      - invoke_llm     : send a system + human message pair to an LLM
    """

    def __init__(self, stage: str, output_dir: Path, debug: bool = False) -> None:
        self.stage = stage
        self.output_dir = output_dir
        self.debug = debug
        self.system_prompt = ""
        self.token_use: list = []

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def save_md(self, filename: str, data: str) -> None:
        """Write *data* to ``output_dir / stage / filename.md``."""
        dest = self.output_dir / self.stage / f"{filename}.md"
        try:
            print(f"saving to {dest}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(data, encoding="utf-8")
        except Exception as exc:
            print(f"save_md error ({exc}): could not write {dest}")

    def collect_files(self, source_path: Path | str, filter_fxn: Callable[[str], bool]) -> list[dict]:
        """Walk *source_path* and return all readable files matching *filter_fxn*.

        Each returned dict has keys ``'path'`` (relative to *source_path*) and
        ``'content'``.  Hidden directories (starting with ``'.'``) are skipped.
        """
        all_files: list[dict] = []
        for root, _, files in os.walk(source_path):
            if "/." in root:
                continue
            for file in files:
                full_path = os.path.join(root, file)
                if filter_fxn(file):
                    try:
                        with open(full_path, "r", encoding="utf-8") as fh:
                            content = fh.read()
                            all_files.append(
                                {
                                    "path": os.path.relpath(full_path, source_path),
                                    "content": content,
                                }
                            )
                    except Exception as exc:
                        print(f"Could not read {full_path}: {exc}")
        return all_files

    def calculate_total_size(self, items: list[str]) -> int:
        """Sum the character lengths of a list of strings."""
        return sum(len(s) for s in items)

    # ------------------------------------------------------------------
    # LLM invocation
    # ------------------------------------------------------------------

    def invoke_llm(self, llm, human_content: str) -> str:
        """Send ``self.system_prompt`` + *human_content* to *llm* and return the response text."""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_content),
        ]
        response = llm.invoke(messages)
        self.token_use.append(response.usage_metadata)
        return response.content


# ---------------------------------------------------------------------------
# Stage 1 – FileSummarizer
# ---------------------------------------------------------------------------

class FileSummarizer(Agent):
    """Stage 1 – walks a source repo, chunks files, and summarizes each chunk.

    File filtering uses ``TEXT_SUFFIXES`` from ``lib/repo_reader.py`` by default.
    Pass a custom list to *extensions* to override.

    Note: ``max_chars_per_chunk`` is very model-dependent:
      ~50 000 for a 4-bit quantized 8B model on an M4,
      ~500 000 for gpt-4o.
    """

    def __init__(
        self,
        repo_path: str | Path,
        output_dir: Path,
        extensions: list[str] | None = None,
        max_chars_per_chunk: int = 50_000,
        debug: bool = False,
        stage: str = STAGES[0],
    ) -> None:
        super().__init__(stage=stage, output_dir=output_dir, debug=debug)
        self.repo_path = Path(repo_path)
        self.extensions = extensions or list(TEXT_SUFFIXES)
        self.max_chars_per_chunk = max_chars_per_chunk
        self.system_prompt = FILE_SUMMARIZER_PROMPT

    def _should_include(self, filename: str) -> bool:
        """Return True if the file's extension is in ``self.extensions``."""
        return any(filename.endswith(ext) for ext in self.extensions)

    def collect_files(self) -> list[dict]:  # type: ignore[override]
        """Walk ``self.repo_path`` and return only files matching ``self.extensions``."""
        return super().collect_files(self.repo_path, self._should_include)

    def create_chunks(self, all_files: list[dict]) -> list[list[dict]]:
        """Create semantically split batches sized for the summarizer context window."""
        chunker = LangChainChunker(max_chunk_chars=self.max_chars_per_chunk)
        return chunker.chunk_files(all_files)

    def summarize_chunk(self, chunk: list[dict], llm) -> str:
        """Send a chunk of files to the LLM and return the structured summary."""
        formatted_content = "\n\n".join(
            f"--- FILE: {f['path']} ---\n{f['content']}" for f in chunk
        )
        return self.invoke_llm(llm, formatted_content)

    def process_all(self, chunks: list[list[dict]], llm) -> list[str]:
        """Summarize every chunk and save each result to the stage output dir."""
        start = time.time()
        processed_sum: list[str] = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i}, with {len(chunk)} files")
            summary = self.summarize_chunk(chunk, llm)
            processed_sum.append(summary)
            print(f"saving summary{i} to {self.stage}")
            self.save_md(f"summary{i}", summary)
            print(f"took {time.time() - start:.1f} seconds")
            start = time.time()
        return processed_sum


# ---------------------------------------------------------------------------
# Stage 2 – ContextManager
# ---------------------------------------------------------------------------

class ContextManager(Agent):
    """Stage 2 – reads scout summaries and recursively reduces them until they
    fit within the architect's context window.
    """

    def __init__(
        self,
        output_dir: Path,
        architect_threshold: int = 20_000,
        debug: bool = False,
        stage: str = STAGES[1],
    ) -> None:
        super().__init__(stage=stage, output_dir=output_dir, debug=debug)
        self.architect_threshold = architect_threshold
        self.scout_path = output_dir / STAGES[0]
        self.system_prompt = CONTEXT_MANAGER_PROMPT

    def collect_files(self) -> list[dict]:  # type: ignore[override]
        """Read all ``.md`` files from the scout output directory."""
        return super().collect_files(self.scout_path, lambda f: f.endswith(".md"))

    def summarize_summaries(self, summary_batch: list[str], llm) -> str:
        """Collapse a group of summaries into a single 'Module Overview'."""
        combined_text = "\n\n".join(summary_batch)
        return self.invoke_llm(llm, combined_text)

    def reduce(self, summaries: list[str], llm) -> list[str]:
        """Recursively shrink summaries until the total size fits the threshold."""
        current_summaries = summaries

        while self.calculate_total_size(current_summaries) > self.architect_threshold:
            print(
                f"Current size {len(str(current_summaries))} exceeds threshold. Reducing..."
            )
            new_summaries: list[str] = []
            chunk_size = 5
            for i in range(0, len(current_summaries), chunk_size):
                batch = current_summaries[i: i + chunk_size]
                reduced_summary = self.summarize_summaries(batch, llm)
                new_summaries.append(reduced_summary)
                self.save_md(f"reduced_sum{i}", reduced_summary)
            current_summaries = new_summaries

        if self.calculate_total_size(current_summaries) < self.architect_threshold:
            print(
                f"Current size {len(str(current_summaries))} does not need reduction"
            )
            self.save_md("reduced_sum", str(current_summaries))
        return current_summaries


# ---------------------------------------------------------------------------
# Stage 3 – ArchitectAgent
# ---------------------------------------------------------------------------

class ArchitectAgent(Agent):
    """Stage 3 – produces and refines a Mermaid architecture diagram.

    ``draft(llm)``:
      - Reads aggregated summaries from ``02_aggregate/``
      - Optionally incorporates an external reference ``.md`` file
      - Produces an initial Mermaid diagram
      - Saves output to ``03_draft/mermaid.md``

    ``revise(llm, arch_md_path=None)``:
      - Reads the draft diagram from ``03_draft/``
      - Reads the critique from ``04_critique/``
      - Reads original aggregated context from ``02_aggregate/`` (source of truth)
      - Optionally incorporates an external reference ``.md`` file
      - Saves the refined output to ``05_refined/mermaid.md``
    """

    def __init__(
        self,
        output_dir: Path,
        arch_md_path: str | Path | None = None,
        debug: bool = False,
        stage: str = STAGES[2],
    ) -> None:
        super().__init__(stage=stage, output_dir=output_dir, debug=debug)
        self.agg_path = output_dir / STAGES[1]       # 02_aggregate/
        self.draft_path = output_dir / STAGES[2]     # 03_draft/
        self.critique_path = output_dir / STAGES[3]  # 04_critique/
        self.arch_md_path = Path(arch_md_path) if arch_md_path else None
        self.system_prompt = ARCHITECT_PROMPT

    def collect_files(self) -> list[dict]:  # type: ignore[override]
        """Read all ``.md`` files from the aggregator output directory."""
        return super().collect_files(self.agg_path, lambda f: f.endswith(".md"))

    def load_arch_md(self) -> str | None:
        """Optionally load an external architecture ``.md`` file as reference context."""
        if self.arch_md_path:
            try:
                return self.arch_md_path.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"Could not read arch_md_path {self.arch_md_path}: {exc}")
        return None

    def draft(self, llm) -> str | None:
        """Generate the initial Mermaid architecture diagram from aggregated summaries."""
        self.stage = STAGES[2]  # 03_draft
        summaries = self.collect_files()
        arch_md = self.load_arch_md()

        if not summaries:
            print("No aggregated summaries found in 02_aggregate/. Run ContextManager first.")
            return None

        parts = []
        agg_text = "\n\n".join(
            f"--- FILE: {f['path']} ---\n{f['content']}" for f in summaries
        )
        parts.append(f"## Aggregated Summaries\n{agg_text}")

        if arch_md:
            parts.append(f"## Reference Architecture (.md file)\n{arch_md}")

        human_content = "\n\n---\n\n".join(parts)

        print(f"Running ArchitectAgent draft on {len(summaries)} summary file(s)...")
        diagram = self.invoke_llm(llm, human_content)
        self.save_md("mermaid", diagram)
        return diagram

    def revise(self, llm, arch_md_path: str | Path | None = None) -> str | None:
        """Refine the Mermaid diagram using critic feedback."""
        self.stage = STAGES[4]  # 05_refined
        if arch_md_path:
            self.arch_md_path = Path(arch_md_path)

        summaries = self.collect_files()  # 02_aggregate/
        drafts = super().collect_files(self.draft_path, lambda f: f.endswith(".md"))
        critiques = super().collect_files(self.critique_path, lambda f: f.endswith(".md"))
        arch_md = self.load_arch_md()

        if not drafts:
            print("No Mermaid diagram found in 03_draft/. Run draft() first.")
            return None
        if not critiques:
            print("No critique found in 04_critique/. Run CritiqueAgent first.")
            return None

        parts = []

        if summaries:
            agg_text = "\n\n".join(
                f"--- FILE: {f['path']} ---\n{f['content']}" for f in summaries
            )
            parts.append(f"## Original Aggregated Summaries (Source of Truth)\n{agg_text}")

        draft_text = "\n\n".join(
            f"--- FILE: {f['path']} ---\n{f['content']}" for f in drafts
        )
        parts.append(f"## Current Mermaid Diagram (Draft)\n{draft_text}")

        critique_text = "\n\n".join(
            f"--- FILE: {f['path']} ---\n{f['content']}" for f in critiques
        )
        parts.append(f"## Critic Feedback\n{critique_text}")

        if arch_md:
            parts.append(f"## Reference Architecture (.md file)\n{arch_md}")

        human_content = "\n\n---\n\n".join(parts)

        print(
            f"Running ArchitectAgent revision with {len(critiques)} critique(s) "
            f"and {len(summaries)} summary file(s)..."
        )
        refined = self.invoke_llm(llm, human_content)
        self.save_md("mermaid", refined)
        return refined


# ---------------------------------------------------------------------------
# Stage 4 – CritiqueAgent
# ---------------------------------------------------------------------------

class CritiqueAgent(Agent):
    """Stage 4 – reviews the Mermaid diagram from the ArchitectAgent and produces
    structured critique feedback to be used as input for the next revision cycle.

    Inputs (read automatically):
      - ``03_draft/*.md``    : The Mermaid diagram(s) produced by ArchitectAgent
      - ``02_aggregate/*.md``: Subsystem summaries for cross-referencing claims
      - ``arch_md_path``     : Optional external reference architecture ``.md`` file

    Output:
      - ``04_critique/critique.md`` : Structured critique (four-section format)
    """

    def __init__(
        self,
        output_dir: Path,
        arch_md_path: str | Path | None = None,
        debug: bool = False,
        stage: str = STAGES[3],
    ) -> None:
        super().__init__(stage=stage, output_dir=output_dir, debug=debug)
        self.draft_path = output_dir / STAGES[2]  # 03_draft/
        self.agg_path = output_dir / STAGES[1]    # 02_aggregate/
        self.arch_md_path = Path(arch_md_path) if arch_md_path else None
        self.system_prompt = CRITIC_PROMPT

    def collect_files(self) -> list[dict]:  # type: ignore[override]
        """Read the Mermaid diagram(s) from the draft stage output directory."""
        return super().collect_files(self.draft_path, lambda f: f.endswith(".md"))

    def collect_context(self) -> list[dict]:
        """Read aggregated subsystem summaries for cross-referencing architectural claims."""
        return super().collect_files(self.agg_path, lambda f: f.endswith(".md"))

    def load_arch_md(self) -> str | None:
        """Optionally load an external architecture ``.md`` file for the critic to investigate."""
        if self.arch_md_path:
            try:
                return self.arch_md_path.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"Could not read arch_md_path {self.arch_md_path}: {exc}")
        return None

    def critique(self, llm) -> str | None:
        """Run the Critic LLM on the Mermaid diagram + context and save the critique."""
        diagrams = self.collect_files()
        context = self.collect_context()
        arch_md = self.load_arch_md()

        if not diagrams:
            print("No Mermaid diagram found in 03_draft/. Run ArchitectAgent first.")
            return None

        parts = []
        if context:
            subsystem_text = "\n\n".join(
                f"--- FILE: {f['path']} ---\n{f['content']}" for f in context
            )
            parts.append(f"## Subsystem Summaries\n{subsystem_text}")

        diagram_text = "\n\n".join(
            f"--- FILE: {f['path']} ---\n{f['content']}" for f in diagrams
        )
        parts.append(f"## Candidate Architecture (Mermaid Diagram)\n{diagram_text}")

        if arch_md:
            parts.append(f"## Reference Architecture (.md file)\n{arch_md}")

        human_content = "\n\n---\n\n".join(parts)

        print(
            f"Running CritiqueAgent on {len(diagrams)} diagram(s) "
            f"with {len(context)} context file(s)..."
        )
        critique_text = self.invoke_llm(llm, human_content)
        self.save_md("critique", critique_text)
        return critique_text
