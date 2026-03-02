# Agentic Architectural Inference

Generate high-level architecture diagrams from a codebase with a multi-agent pipeline and a falsification-first Critic loop.

## What This Builds

Input: local repository path  
Output: Mermaid architecture diagram + evidence-backed critique reports

Pipeline:
1. `File Summarizer Agent`: summarizes each source file for architectural signals.
2. `Context Manager Agent`: groups file summaries into subsystem partitions.
3. `Architect Agent`: proposes components/edges + Mermaid diagram.
4. `Critic Agent`: attempts to disprove weak edges, then forces architecture revision.

## Project Layout

```text
aai/
  cli.py                 # entrypoint
  pipeline.py            # orchestration
  agents.py              # agent calls
  prompts.py             # loads prompts from prompts/*.md
  repo_reader.py         # repository scanning
  llm.py                 # OpenAI API wrapper
prompts/
  file-summarizer.md
  context-manager.md
  architect.md
  architect-revision.md
  critic-agent-v2.md
  reference/             # legacy/reference prompt variants
archagent-prompts.txt    # reference-only index to split prompt files
requirements.txt
```

## Prerequisites

- Python 3.10+
- OpenAI API key
- Internet access for OpenAI API calls

## Install

Run from this repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your API key:

```bash
export OPENAI_API_KEY="YOUR_KEY_HERE"
```

## Run

Analyze this repo:

```bash
python3 -m aai.cli \
  --repo-path . \
  --model gpt-4.1-mini \
  --critic-rounds 2 \
  --out-dir outputs/latest
```

Analyze another local repo:

```bash
python3 -m aai.cli \
  --repo-path /absolute/path/to/target/repo \
  --model gpt-4.1-mini \
  --max-files 150 \
  --critic-rounds 3 \
  --out-dir outputs/target-repo
```

Disable step-by-step logs:

```bash
python3 -m aai.cli --repo-path /absolute/path/to/repo --quiet
```

## Outputs

Each run writes:

- `architecture.mmd`: final Mermaid flowchart
- `architecture.json`: structured components/edges/evidence
- `critic_reports.json`: raw critic rounds
- `critic_report.md`: human-readable critique summary
- `file_summaries.json`: per-file summaries
- `partitions.json`: subsystem partitions
- `run_stats.json`: runtime and token counters

## New Critic Agent Design

`prompts/critic-agent-v2.md` introduces a stricter falsification rubric:
- challenges every edge direction and label
- rejects unsupported flow claims
- identifies missing mediator components
- proposes explicit edge actions: `keep`, `downgrade_confidence`, `remove`, `needs_more_evidence`

Runtime prompts are loaded from `prompts/*.md` via `aai/prompts.py`, so each agent is editable independently.

## How To Tune Quality

- Increase `--critic-rounds` to reduce false positives.
- Reduce `--max-files` for very large repos to control cost first, then scale up.
- Adjust prompts directly in `prompts/file-summarizer.md`, `prompts/context-manager.md`, `prompts/architect.md`, `prompts/architect-revision.md`, and `prompts/critic-agent-v2.md`.
- Keep evidence requirements strict for higher trust diagrams.

## Suggested Next Improvements

1. Add tree-sitter/static analysis tools for stronger dependency evidence.
2. Render Mermaid to PNG/SVG in CI for docs publishing.
3. Add evaluation harness against hand-curated architecture ground truth.
