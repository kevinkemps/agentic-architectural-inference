## file_path
aai copy/repo_reader.py

## purpose
Scans a repository to identify text files and extracts their content.

## exports
- SourceFile

## dependencies
- `os`
- `pathlib`
- `dataclasses`

## architecture_signals
- database access: none
- writes db: none
- writes file: none
- publishes message: none
- calls external api: none
- mutates shared state: none

## confidence
0.8

## file_path
aai copy/__init__.py

## purpose
Provides an initialization for the Agentic architectural inference package.

## exports
- none

## dependencies
- none

## architecture_signals
- none

## confidence
0.9

## file_path
aai copy/llm.py

## purpose
Provides helper functions for interacting with the OpenAI API.

## exports
- LLMStats
- build_client
- reset_stats
- snapshot_stats
- _extract_usage
- _parse_json_response
- complete_json

## dependencies
- `openai`
- `copy`
- `json`
- `re`
- `time`

## architecture_signals
- API handlers: complete_json
- database access: none
- writes db: none
- writes file: none
- publishes message: none
- calls external api: complete_json
- mutates shared state: _STATS

## confidence
0.9

## file_path
aai copy/prompts.py

## purpose
Loads and provides prompt templates for various agents.

## exports
- FILE_SUMMARIZER_PROMPT
- CONTEXT_MANAGER_PROMPT
- ARCHITECT_PROMPT
- CRITIC_PROMPT
- ARCHITECT_REVISION_PROMPT

## dependencies
- `pathlib`

## architecture_signals
- none

## confidence
0.9