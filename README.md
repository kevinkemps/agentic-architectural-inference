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

## Setup

### 1. Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env_example .env
```

Edit `.env` to configure your LLM provider:

#### Example Anthropic Claude Configuration
ANTHROPIC_API_KEY=sk-ant-xxxx
ANTHROPIC_MODEL=claude-sonnet-4-5
LLM_PROVIDER=claude

#### Note for Mac users
Instead of ollama, mlx provides significant speed improvements (2x)
Run with the 'local' parameter set to use mlx. Otherwise use ollama

#### Optimization Settings
```bash
# Set to 'static' to skip LLM for the first step (faster, larger single context)
FIRST_AGENT_MODE=llm
```

### AGENTS.md setup
In VSCode:
Command Pallet: Chat: Chat Settings
- Search agent
- Add ./ to the agent file location
- Search agents
- Enable AGENTS.md file

## Usage

### Basic Commands

1. mkdir code_base
2. git clone repo into code_base
3. cd aai
Analyze the current repository in ../code_base:

```bash
python3 -m cli
```

Analyze a specific repository:

```bash
python3 -m cli --repo-path /path/to/your/repo
```

### Advanced Options

#### Chunking and Context Control
Control how files are processed for different model capabilities:

```bash
# For local 8B models (smaller chunks)
python3 -m cli --max-chars-per-chunk 50000

# For powerful models like GPT-4o (larger chunks)
python3 -m cli --max-chars-per-chunk 500000

# Adjust architect context threshold
python3 -m cli --architect-threshold 30000
```

#### Critique and Quality Control
Improve diagram accuracy with multiple critique rounds:

```bash
# Single critique round (default)
python3 -m cli --critic-rounds 1
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

After `architecture.mmd` is written, the pipeline also attempts to render PNG/SVG
copies into `docs/diagrams` for docs publishing 

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
