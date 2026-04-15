## file_path
aai copy/agents.py

## purpose
Implements various functions for summarizing files, partitioning summaries, proposing architecture, and handling critic reviews.

## exports
- summarize_file
- partition_summaries
- propose_architecture
- critic_review
- revise_architecture

## dependencies
- `openai.OpenAI`
- `json`
- `dataclasses`
- `typing`
- `aai copy.prompts`
- `aai copy.repo_reader.SourceFile`
- `aai copy.pipeline.run_pipeline`
- `aai copy.pipeline.write_artifacts`

## architecture_signals
- API handlers: `summarize_file`, `partition_summaries`, `propose_architecture`, `critic_review`, `revise_architecture`
- Database access: none
- Queues: none
- Jobs: none
- Messaging: none
- Config: `model`, `max_files`, `max_chars_per_file`, `critic_rounds`
- Orchestration: `run_pipeline`, `write_artifacts`
- External integrations: `openai.OpenAI`

## confidence
0.9

## file_path
aai copy/cli.py

## purpose
Provides a command-line interface for running the multi-agent architecture inference process.

## exports
- parse_args
- main

## dependencies
- `argparse`
- `pathlib.Path`
- `aai copy.pipeline.run_pipeline`
- `aai copy.pipeline.write_artifacts`

## architecture_signals
- CLI command: `main`
- Database access: none
- Queues: none
- Jobs: none
- Messaging: none
- Config: `repo_path`, `model`, `max_files`, `max_chars_per_file`, `critic_rounds`, `out_dir`, `quiet`
- Orchestration: `parse_args`, `main`
- External integrations: `SystemExit`

## confidence
0.9

## entrypoints
- `cli command`: `main`

## side_effects
- writes db: none
- writes file: `write_artifacts`
- publishes message: none
- calls external api: `SystemExit`
- mutates shared state: none

## risk_or_ambiguity
- none