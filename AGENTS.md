# AGENTS

This document defines the standard agent roles, handoffs, and maintenance rules for this repository.

Always note the below in the chat when it is being referenced.
"AGENTS.md file is in context."
Always note the current model that is being used.

## Purpose

The pipeline in this project infers software architecture from source code using staged LLM agents. This file is the canonical contributor guide for:

- agent responsibilities
- stage input and output contracts
- readability and documentation expectations

For prompt-level files and future agent variants, use `docs/agents/`.

## Repository Scope

Primary implementation lives in `aai/`:

- `aai/cli.py`: CLI entrypoint and runtime flags
- `aai/pipeline.py`: pipeline orchestration for stage execution and critique loops
- `aai/lib/agents.py`: concrete agent classes and file handoffs
- `aai/lib/architecture_schema.py`: canonical architecture schema normalization and Mermaid rendering using controlled categories plus repo-specific modules
- `aai/lib/prompts.py`: prompt loading from `prompts/*.md`
- `aai/lib/repo_reader.py`: source file scanning and filtering rules
- `aai/evaluation/service.py`: repository-vs-diagram evaluation and scoring
- `aai/webapp.py`: local browser UI for generation and evaluation

Prompt definitions live in `prompts/` and are loaded at runtime.

## Build and Run

Primary workflow:

```bash
cd aai
python3 -m cli
```

Common variants:

```bash
python3 -m cli --repo-path /path/to/repo
python3 -m cli --critic-rounds 3
python3 -m cli --max-chars-per-chunk 500000
python3 -m cli --mode single_prompt
```

Environment setup and provider configuration are documented in `README.md`.

## Conventions and Pitfalls

- Treat `AGENTS.md` as the architecture and stage contract source of truth.
- Keep prompt behavior changes in `prompts/*.md`; runtime prompt loading is implemented in `aai/lib/prompts.py`.
- Keep stage handoffs explicit via filesystem artifacts under `aai/output_analysis/`.
- Prefer evidence-backed edits to architecture prompts; do not add speculative components or edges.
- Keep evaluation scoring prompts in `prompts/*.md`; do not hardcode rubric changes in runtime code.
- Keep repo-specific question generation rules in `aai/evaluation/eval_questions.md` and `prompts/evaluation-question-generator.md`.
- `LLM_PROVIDER=local` relies on MLX server behavior in `aai/lib/llm.py`; local model runs may fail if server startup fails.
- Mermaid rendering depends on external tooling (`mmdc` or Playwright fallback) in `aai/lib/mermaid_renderer.py`; if unavailable, rendering can be skipped.

## Linked References

- Setup and runtime usage: `README.md`
- Prompt contracts: `prompts/file-summarizer.md`, `prompts/context-manager.md`, `prompts/architect.md`, `prompts/critic-agent-v2.md`, `prompts/designer-agent.md`
- Pipeline orchestration: `aai/pipeline.py`
- Agent implementations: `aai/lib/agents.py`
- Evaluation runtime: `aai/evaluation/service.py`
- Core evaluation question contract: `aai/evaluation/eval_questions.md`
- Critique evolution guide: `docs/agents/critique-evolution-guide.md`

## Stage Contract

The pipeline stages are fixed in code as:

1. `01_scout`
2. `02_aggregate`
3. `03_draft`
4. `04_critique`
5. `05_refined`
6. `06_visual`

Output root defaults to `aai/output_analysis/` when running from the `aai/` directory.

Auxiliary evaluation artifacts may also be written under a run-local `evaluation/`
directory without changing the fixed stage list above.
This includes generated repo-specific question files used for scoring.
Web app runs may also write `analysis_summary.json` per run, and debug comparison
runs may write a combined `debug_analysis.json` at the run root.

## Agent Definitions

### 1) FileSummarizer (Scout)

- Class: `FileSummarizer`
- Reads: repository source files filtered by text extensions
- Writes: `01_scout/summary*.md`
- Responsibility: summarize implementation-level files into architecture signals

### 2) ContextManager (Aggregate)

- Class: `ContextManager`
- Reads: `01_scout/*.md`
- Writes: `02_aggregate/reduced_sum*.md`
- Responsibility: recursively reduce summaries until architect context is below token threshold

### 3) ArchitectAgent (Draft + Revise)

- Class: `ArchitectAgent`
- Draft reads: `02_aggregate/*.md`
- Draft writes: `03_draft/architecture.json`, `03_draft/mermaid.md`
- Revise reads: `02_aggregate/*.md`, `03_draft/*.md`, `04_critique/*.md`
- Revise writes: `05_refined/architecture.json`, `05_refined/mermaid.md`
- Responsibility: produce and revise a canonical architecture spec with controlled categories and repo-specific modules, then render a standardized Mermaid diagram from that spec

### 4) CritiqueAgent (Falsification)

- Class: `CritiqueAgent`
- Reads: `03_draft/*.md` and `02_aggregate/*.md`
- Writes: `04_critique/critique.md`
- Responsibility: challenge unsupported claims, edge directions, and missing mediators before refinement
- Optional input: `evolved_prompt_path` to load improved prompts from evolution cycles

### 5) Renderer (Visual)

- Node: render step in `aai/pipeline.py`
- Reads: `03_draft/mermaid.md`, `05_refined/mermaid.md`
- Writes: `06_visual/mermaid_draft.mmd`, `06_visual/mermaid_refined.mmd` and rendered assets when available
- Responsibility: extract Mermaid code blocks and render visual artifacts

## Runtime Behavior

- Orchestration is managed in `aai/pipeline.py`.
- Flow is linear until critique, then loops critique -> revise.
- The CLI and web app also support a `single_prompt` baseline mode that skips scout,
  aggregate, and critique loops and writes a draft diagram from one repository digest prompt.
- Architect generation is standardized in two steps:
  - the LLM produces a canonical architecture JSON spec
  - runtime code normalizes category/module structure and renders Mermaid deterministically
- Loop exits when either:
  - no critique output is returned, or
  - completed rounds meet `--critic-rounds`.
- The web app evaluates each selected diagram by comparing repository-grounded answers
  against diagram-grounded answers using `aai/evaluation/eval_questions.md`.
- The web app can also run a debug comparison mode that executes:
  - `single_prompt`
  - `multi_agent` with critic off
  - `multi_agent` with critic on
  and returns all three diagrams plus their analyses in one response.
- Evaluation first loads fixed cross-repository questions, then generates a separate
  repo-specific question file from the scanned repository and scores against the combined set.

## Readability Standard (Team Requirement)

All agent and pipeline changes should prioritize readability:

- use clear names for stage data and methods
- keep functions focused and avoid hidden side effects
- prefer short docstrings that explain intent and contract
- preserve explicit file handoff paths between stages
- ask about overly-compressed logic in orchestration and agent methods

## Documentation Sync Policy

When code changes, update docs in the same pull request.

Minimum sync checklist:

1. If stages, directories, or filenames change: update this file and `README.md`.
2. If CLI flags or defaults change: update `README.md` usage/examples.
3. If prompt loading behavior changes: update `README.md` and note affected prompt files.
4. If agent responsibilities or handoffs change: update this file first.

## Where to Store Agent Documentation

Use `docs/agents/` for:

- alternative agent specs
- experiment notes
- prompt strategy docs
- review checklists and governance docs

Keep this root `AGENTS.md` as the stable, high-level contract.
