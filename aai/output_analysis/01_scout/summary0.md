## file_path
aai copy/cli.py

## purpose
Provides a command-line interface for running the multi-agent architecture inference pipeline.

## exports
- `parse_args`
- `main`

## dependencies
- `argparse`
- `pathlib`
- `aai copy.pipeline.run_pipeline`
- `aai copy.pipeline.write_artifacts`

## architecture_signals
- **entrypoints**: `main`
- **side_effects**: writes files to the specified output directory

## confidence
0.9

## file_path
aai copy/pipeline.py

## purpose
Orchestration pipeline for the multi-agent architecture inference process.

## exports
- `run_pipeline`
- `write_artifacts`

## dependencies
- `aai copy.agents.summarize_file`
- `aai copy.agents.partition_summaries`
- `aai copy.agents.propose_architecture`
- `aai copy.agents.critic_review`
- `aai copy.agents.revise_architecture`
- `aai copy.llm.build_client`
- `aai copy.llm.reset_stats`
- `aai copy.llm.snapshot_stats`
- `aai copy.repo_reader.load_readme`
- `aai copy.repo_reader.load_repo_files`
- `aai copy.mermaid_renderer.render_mermaid_file`

## architecture_signals
- **entrypoints**: `run_pipeline`
- **side_effects**: writes JSON and Mermaid files to the specified output directory

## confidence
0.9

## file_path
aai copy/agents.py

## purpose
Implements various agents for the multi-agent architecture inference process.

## exports
- `RunArtifacts`
- `summarize_file`
- `partition_summaries`
- `propose_architecture`
- `critic_review`
- `revise_architecture`

## dependencies
- `aai copy.llm.complete_json`
- `aai copy.prompts.FILE_SUMMARIZER_PROMPT`
- `aai copy.prompts.CONTEXT_MANAGER_PROMPT`
- `aai copy.prompts.ARCHITECT_PROMPT`
- `aai copy.prompts.CRITIC_PROMPT`
- `aai copy.prompts.ARCHITECT_REVISION_PROMPT`
- `aai copy.agents.RunArtifacts`
- `aai copy.agents.summarize_file`
- `aai copy.agents.partition_summaries`
- `aai copy.agents.propose_architecture`
- `aai copy.agents.critic_review`
- `aai copy.agents.revise_architecture`

## architecture_signals
- **entrypoints**: `summarize_file`, `partition_summaries`, `propose_architecture`, `critic_review`, `revise_architecture`
- **side_effects**: updates LLM stats

## confidence
0.9

## file_path
aai copy/repo_reader.py

## purpose
Provides helpers for scanning repositories and reading files.

## exports
- `TEXT_SUFFIXES`
- `SKIP_DIRS`
- `SourceFile`
- `load_repo_files`
- `load_readme`

## dependencies
- `os`
- `pathlib`
- `dataclasses`
- `aai copy.prompts._load_prompt`

## architecture_signals
- **entrypoints**: `load_repo_files`, `load_readme`
- **side_effects**: none

## confidence
0.8

## file_path
aai copy/llm.py

## purpose
Provides helpers for interacting with the OpenAI API.

## exports
- `LLMStats`
- `build_client`
- `reset_stats`
- `snapshot_stats`
- `complete_json`
- `_extract_usage`
- `_parse_json_response`

## dependencies
- `os`
- `re`
- `time`
- `dataclasses`
- `typing`
- `aai copy.prompts._load_prompt`

## architecture_signals
- **entrypoints**: `build_client`, `reset_stats`, `snapshot_stats`, `complete_json`
- **side_effects**: updates LLM stats

## confidence
0.9

## file_path
aai copy/prompts.py

## purpose
Provides prompt templates for the multi-agent architecture inference pipeline.

## exports
- `FILE_SUMMARIZER_PROMPT`
- `CONTEXT_MANAGER_PROMPT`
- `ARCHITECT_PROMPT`
- `CRITIC_PROMPT`
- `ARCHITECT_REVISION_PROMPT`

## dependencies
- `pathlib`
- `aai copy.prompts._load_prompt`

## architecture_signals
- **entrypoints**: none
- **side_effects**: none

## confidence
0.8

## file_path
aai copy/mermaid_renderer.py

## purpose
Provides helpers for rendering Mermaid diagrams.

## exports
- `render_mermaid_file`

## dependencies
- `subprocess`
- `shutil`
- `sys`
- `pathlib`

## architecture_signals
- **entrypoints**: `render_mermaid_file`
- **side_effects**: writes SVG and PNG files to the specified output directory

## confidence
0.8