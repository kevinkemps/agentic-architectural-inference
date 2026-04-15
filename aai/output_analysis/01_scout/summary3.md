## file_path
aaicopy/mermaid_renderer.py

## purpose
Provides helper functions for rendering Mermaid diagrams to SVG and PNG formats for documentation purposes.

## exports
- render_mermaid_file
- _run_command
- _render_with_mmdc
- _ensure_playwright_chromium
- _looks_like_missing_browser_error

## dependencies
- subprocess
- shutil
- pathlib
- typing
- sys

## architecture_signals
- config: `render_mermaid_file` specifies default output directory and stem.
- orchestration: `_run_command` and `_render_with_mmdc` orchestrate subprocess calls.
- external integrations: `mmdc` and `playwright` are external tools used for rendering and browser installation.

## confidence
0.9

## side_effects
- writes file: `render_mermaid_file` writes SVG and PNG files to the specified output directory.

## risk_or_ambiguity
- none