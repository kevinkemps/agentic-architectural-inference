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


# Rule: Context Archival
IF the conversation involves making changes to code or CI/CD debugging:
THEN, before concluding the session or moving to a new task:
  1. Generate a concise "Test Insight" block.
  2. Append this block to `.chat_stash/logs/evolution.md`.
  3. Format the block as follows:
     - Date: [ISO Date]
     - Component: [e.g., Aggregator, Signal Processor]
     - Problem: [What was failing or missing?]
     - Solution Pattern: [The specific logic/mock used to fix it]
     - Hardware Note: [Relevant VRAM/M-series/NVIDIA specifics]
Note that this is done at the end of the chat.

# Rule: Context clearing and evolution:
IF `.chat_stash/logs/evolution.md` has 2 or more blocks:
1.  Read the ENTIRE File
2. Summarrize if there are lessons to be learned from the conversations or repeated patterns.
3. Summarrize the pattern in this file under `Notes from previous chats:`
4. Clear `.chat_stash/logs/evolution.md`

## Repository Scope

Primary implementation lives in `aai/`:

- `aai/cli.py`: CLI entrypoint and runtime flags
- `aai/pipeline.py`: LangGraph orchestration for stage execution and critique loops
- `aai/lib/agents.py`: concrete agent classes and file handoffs
- `aai/lib/prompts.py`: prompt loading from `prompts/*.md`
- `aai/lib/repo_reader.py`: source file scanning and filtering rules

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
```

Environment setup and provider configuration are documented in `README.md`.

## Conventions and Pitfalls

- Treat `AGENTS.md` as the architecture and stage contract source of truth.
- Keep prompt behavior changes in `prompts/*.md`; runtime prompt loading is implemented in `aai/lib/prompts.py`.
- Keep stage handoffs explicit via filesystem artifacts under `aai/output_analysis/`.
- Prefer evidence-backed edits to architecture prompts; do not add speculative components or edges.
- `LLM_PROVIDER=local` relies on MLX server behavior in `aai/lib/llm.py`; local model runs may fail if server startup fails.
- Mermaid rendering depends on external tooling (`mmdc` or Playwright fallback) in `aai/lib/mermaid_renderer.py`; if unavailable, rendering can be skipped.

## Linked References

- Setup and runtime usage: `README.md`
- Prompt contracts: `prompts/file-summarizer.md`, `prompts/context-manager.md`, `prompts/architect.md`, `prompts/critic-agent-v2.md`, `prompts/designer-agent.md`
- Pipeline orchestration: `aai/pipeline.py`
- Agent implementations: `aai/lib/agents.py`
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
- Draft writes: `03_draft/mermaid.md`
- Revise reads: `02_aggregate/*.md`, `03_draft/*.md`, `04_critique/*.md`
- Revise writes: `05_refined/mermaid.md`
- Responsibility: produce and revise Mermaid architecture based on evidence and critic feedback

### 4) CritiqueAgent (Falsification)

- Class: `CritiqueAgent`
- Reads: `03_draft/*.md` and `02_aggregate/*.md`
- Writes: `04_critique/critique.md`
- Responsibility: challenge unsupported claims, edge directions, and missing mediators before refinement
- Optional input: `evolved_prompt_path` to load improved prompts from evolution cycles

### 4a) CritiqueEvaluator (Feedback Collection)

- Class: `CritiqueEvaluator`
- Reads: `04_critique/critique.md`, `aai/evaluation/eval_questions.md`
- Writes: `04_critique/feedback.json` (evaluation results per run)
- Responsibility: measure critique effectiveness using heuristic metrics (effectiveness, actionability, false positive risk)
- Triggered by: `--eval-questions-path` CLI flag
- Output format: JSON with keys `effectiveness_score`, `actionability_score`, `false_positive_risk`, `coverage`

### 4b) DesignerAgent (Critique Strategy Evolution)

- Class: `DesignerAgent`
- Reads: `04_critique/feedback.json`, `03_draft/*.md`, `02_aggregate/*.md`, `04_critique/critique.md`
- Writes: `04_critique/designer_proposals.md`, `04_critique/evolution_history.json`
- Responsibility: analyze failure patterns in critiques and propose prompt refinements
- Triggered by: `--enable-designer` CLI flag (requires `--eval-questions-path`)
- Process:
  1. Loads feedback history; identifies patterns (low effectiveness, high false positives, low actionability)
  2. Calls LLM to generate refinement proposals based on pattern analysis
  3. Tracks prompt versions in `evolution_history.json` with metrics
  4. Saves human-readable proposals to `designer_proposals.md`
- Output: Versioned evolved prompts (e.g., `prompts/critic-agent-v2-evolved-v1.md`) managed by operator

### 5) Renderer (Visual)

- Node: render step in `aai/pipeline.py`
- Reads: `03_draft/mermaid.md`, `05_refined/mermaid.md`
- Writes: `06_visual/mermaid_draft.mmd`, `06_visual/mermaid_refined.mmd` and rendered assets when available
- Responsibility: extract Mermaid code blocks and render visual artifacts

## Runtime Behavior

- Orchestration is managed by LangGraph in `aai/pipeline.py`.
- Flow is linear until critique, then loops critique -> revise.
- Loop exits when either:
  - no critique output is returned, or
  - completed rounds meet `--critic-rounds`.
- After critique loop exits:
  - If `--eval-questions-path` provided: CritiqueEvaluator runs, produces feedback.json
  - If `--enable-designer` enabled: DesignerAgent runs, analyzes feedback, produces designer_proposals.md and evolution_history.json

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


# Notes from previous chats:
