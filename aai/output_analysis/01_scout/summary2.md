## pipeline.py
```markdown
## purpose
Orchestrates the pipeline for summarizing code files, partitioning summaries, and refining architectural proposals.

## exports
- run_pipeline
- _log
- _normalize_architecture_payload
- _sanitize_mermaid_text
- _build_mermaid_from_graph
- write_artifacts

## dependencies
- .agents: criticize, partition_summaries, propose_architecture, revise_architecture, summarize_file
- .llm: build_client, reset_stats, snapshot_stats
- .mermaid_renderer: render_mermaid_file
- .repo_reader: load_readme, load_repo_files

## architecture_signals
- orchestration: run_pipeline
- database_access: none
- writes file: architecture.mmd, architecture.json, critic_reports.json, file_summaries.json, partitions.json, run_stats.json
- renders diagram: architecture.mmd to docs/diagrams

## confidence
0.9
```

## risk_or_ambiguity
- The file contains a lot of internal dependencies and custom functions, which may make it harder to infer the exact architecture signals without more context.
- The `write_artifacts` function writes several JSON and Markdown files, but the exact content and usage of these files are not detailed in the code.
- The `critic_review` and `revise_architecture` functions are used to refine the architecture, but the exact nature of the feedback and the process are not detailed.