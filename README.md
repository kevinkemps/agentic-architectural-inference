# Agentic Architectural Inference

Generate high-level architecture diagrams from source code with either a staged multi-agent pipeline or a single-prompt baseline, then score the diagram against repository-grounded answers.

## What This Builds

Input: a local repository path

Outputs per run:
- canonical architecture JSON
- draft Mermaid diagram
- refined Mermaid diagram when the critic is enabled
- rendered Mermaid assets when `mmdc` is available
- evaluation answer sets and a scorecard
- latency and token summaries

## Project Layout

```text
aai/
  cli.py
  pipeline.py
  webapp.py
  evaluation/
    eval_questions.md
    service.py
  lib/
    agents.py
    architecture_schema.py
    llm.py
    logging_config.py
    mermaid_renderer.py
    prompts.py
    repo_reader.py
prompts/
  architect.md
  context-manager.md
  critic-agent-v2.md
  evaluation-diagram-answers.md
  evaluation-judge.md
  evaluation-question-generator.md
  evaluation-repo-answers.md
  file-summarizer.md
  single-shot-architect.md
AGENTS.md
requirements.txt
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env_example .env
```

Set `LLM_PROVIDER` plus the provider-specific model and API key values in `.env`.

## CLI Usage

Run the default multi-agent pipeline:

```bash
.venv/bin/python -m aai.cli --repo-path /path/to/repo
```

Disable the critic loop:

```bash
.venv/bin/python -m aai.cli --repo-path /path/to/repo --critic-rounds 0
```

Run the single-prompt baseline:

```bash
.venv/bin/python -m aai.cli --repo-path /path/to/repo --mode single_prompt
```

Useful options:

```bash
.venv/bin/python -m aai.cli --out-dir aai/output_analysis/custom_run
.venv/bin/python -m aai.cli --max-chars-per-chunk 500000
.venv/bin/python -m aai.cli --architect-threshold 30000
.venv/bin/python -m aai.cli --arch-md-path /path/to/reference_architecture.md
```

## Web App

Launch the local workbench:

```bash
.venv/bin/python -m aai.webapp
```

Then open `http://127.0.0.1:8787`.

The UI supports:
- repo path input
- multi-agent vs single-prompt mode
- critic on/off
- debug comparison mode that runs single-shot, critic-off, and critic-on together
- diagram rendering
- per-question evaluation scores
- critic-change highlight text for critic-enabled runs
- save analysis as JSON
- latency and token totals

## Evaluation Model

Evaluation uses:
- the fixed core question set in `aai/evaluation/eval_questions.md`
- an automatically generated repo-specific question set produced from the scanned repository

The evaluation question sets are designed to test architecture-level understanding
that a high-level diagram can reasonably answer, rather than line-level code detail.

For each run:
1. The system loads the fixed core questions.
2. The system generates 5 to 10 repo-specific questions from the repository digest.
3. The model answers the combined question set from repository traversal evidence.
4. The model answers the same combined question set from the generated Mermaid diagram only.
5. A judge model compares the two answer sets and scores each question from `0` to `5`.
6. The overall score is normalized to `0-100`.

This supports:
- RQ1: compare multi-agent runs against `--mode single_prompt`
- RQ2: compare critic-enabled runs against `--critic-rounds 0`
- RQ3: compare `total_duration_seconds` and token usage with and without the critic

## Output Structure

Single CLI runs write to the chosen `--out-dir`.

The web app writes timestamped runs under `aai/output_analysis/runs/`.

Each run contains:

```text
<run_dir>/
  01_scout/
  02_aggregate/
  03_draft/
    architecture.json
    mermaid.md
  04_critique/
    critique.md
  05_refined/
    architecture.json
    mermaid.md
  06_visual/
    mermaid_draft.mmd
    mermaid_draft.svg|png
    mermaid_refined.mmd
    mermaid_refined.svg|png
  evaluation/
    core_eval_questions.md
    repo_specific_eval_questions.md
    combined_eval_questions.md
    repo_answers.json
    diagram_answers.json
    scorecard.json
    analysis_summary.json
```

Some directories remain empty for `single_prompt` runs or when the critic is disabled.
Debug comparison runs also write a combined `debug_analysis.json` file at the run root.

## Notes

- Prompt behavior lives in `prompts/*.md`.
- Diagram generation is standardized by having the architect emit a canonical architecture JSON spec with controlled categories and repo-specific modules, then rendering Mermaid deterministically from that spec.
- Mermaid rendering requires `mmdc`. If Chromium is missing, the renderer attempts a Playwright install and retries.
- The current environment shows warnings with Python 3.14 from `langchain_core`; Python 3.10-3.12 is the safer target for actual runs.
