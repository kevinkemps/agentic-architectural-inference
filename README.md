# Agentic Architectural Inference

Generate architecture diagrams from source code using a staged, multi-agent pipeline with critique-and-revision loops.

## What This Builds

Input: a local repository path  
Output: draft and refined Mermaid architecture diagrams, critique feedback, and rendered visual assets

Pipeline stages:
1. FileSummarizer (01_scout): summarizes source files into architecture signals.
2. ContextManager (02_aggregate): reduces scout summaries into architect-sized context.
3. ArchitectAgent draft (03_draft): creates an initial Mermaid architecture.
4. CritiqueAgent (04_critique): challenges unsupported claims and weak edges.
5. ArchitectAgent refine (05_refined): revises the draft using critique feedback.
6. Renderer (06_visual): extracts Mermaid source and attempts PNG/SVG rendering.

## Project Layout

```text
aai/
  cli.py                   # CLI entrypoint
  pipeline.py              # stage orchestration
  eval_runner.py           # evaluation metrics runner
  lib/
    agents.py
    llm.py
    logging_config.py
    mermaid_renderer.py
    prompts.py
    repo_reader.py
  evaluation/
    eval_questions.md
prompts/
  file-summarizer.md
  context-manager.md
  architect.md
  critic-agent-v2.md
  designer-agent.md
requirements.txt
AGENTS.md
```

## Prerequisites

- Python 3.10+

## Setup

### 1. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env_example .env
```

Then edit .env. Supported providers are:
- local
- local-ollama
- claude
- openai

Minimal OpenAI example:

```bash
OPENAI_API_KEY=sk-proj-xxxx
OPENAI_MODEL=gpt-4o
LLM_PROVIDER=openai
```

## Running the Pipeline

Run from inside the aai directory:

```bash
cd aai
python3 -m cli
```

Analyze a specific repository:

```bash
python3 -m cli --repo-path /path/to/repo
```

Useful options:

```bash
# Output root (default: output_analysis; stage outputs are cleared before each run)
python3 -m cli --out-dir output_analysis

# Chunk and context controls
python3 -m cli --max-chars-per-chunk 500000
python3 -m cli --architect-threshold 30000

# Critique loops
python3 -m cli --critic-rounds 3

# Optional external architecture reference
python3 -m cli --arch-md-path /path/to/reference_architecture.md


## Output Structure

By default, each run clears and then rewrites aai/output_analysis/ with stage directories:

```text
output_analysis/
  01_scout/
    summary*.md
  02_aggregate/
    reduced_sum*.md
  03_draft/
    mermaid.md
  04_critique/
    critique.md
    feedback.json             # evaluation feedback output
    designer_proposals.md     # designer proposal output
    evolution_history.json    # designer version history
  05_refined/
    mermaid.md
  06_visual/
    mermaid_draft.mmd
    mermaid_refined.mmd
    mermaid_draft.svg|png     # when Mermaid rendering succeeds
    mermaid_refined.svg|png   # when Mermaid rendering succeeds
```

## Onboarding Evaluation

The repository also includes a Copilot agent to help evaluate the block diagram output: [`.github/agents/evaluation-onboarding.agent.md`].

### Instructions on use
In Copilot Chat, pick the Evaluator agent. Enter "run evaluation". It should read only [aai/output_analysis/06_visual/mermaid_refined.mmd] agentic_architectural_inference/aai/output_analysis/06_visual/mermaid_refined.mmd), answer the questions in [aai/evaluation/eval_questions.md], and write its report to [aai/evaluation/evaluation.md].

To change the onboarding questions, edit [aai/evaluation/eval_questions.md]. You can add new questions there or replace the existing ones to match the evaluation you want the agent to perform.


## Notes

- Prompts are loaded at runtime from prompts/*.md via aai/lib/prompts.py.
- The onboarding evaluator is separate from the main pipeline output under aai/output_analysis/.
- Mermaid rendering requires mmdc (Mermaid CLI). If Chromium is missing, the renderer attempts a Playwright install and retries.
