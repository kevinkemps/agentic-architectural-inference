"""Mermaid rendering helpers for docs publishing."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def _run_command(command: Sequence[str]) -> None:
    subprocess.run(command, check=True, capture_output=True, text=True)


def _render_with_mmdc(mermaid_file: Path, output_file: Path) -> None:
    _run_command(
        [
            "mmdc",
            "-i",
            str(mermaid_file),
            "-o",
            str(output_file),
        ]
    )


def _ensure_playwright_chromium() -> None:
    _run_command([sys.executable, "-m", "playwright", "install", "chromium"])


def _looks_like_missing_browser_error(stderr: str) -> bool:
    lowered = stderr.lower()
    return (
        "browser executable" in lowered
        or "failed to launch browser" in lowered
        or "playwright" in lowered and "install" in lowered
        or "chromium" in lowered and "not found" in lowered
    )


def render_mermaid_file(
    mermaid_file: str | Path,
    docs_dir: str | Path = "docs/diagrams",
    output_stem: str | None = None,
) -> list[Path]:
    """Render a Mermaid .mmd file to PNG and SVG under docs/diagrams.

    Raises RuntimeError when mmdc is unavailable or rendering fails.
    """
    source = Path(mermaid_file).resolve()
    if not source.exists():
        raise RuntimeError(f"Mermaid file not found: {source}")

    docs_output = Path(docs_dir).resolve()
    docs_output.mkdir(parents=True, exist_ok=True)

    stem = output_stem or source.stem
    svg_path = docs_output / f"{stem}.svg"
    png_path = docs_output / f"{stem}.png"

    if shutil.which("mmdc") is None:
        raise RuntimeError(
            "Mermaid CLI 'mmdc' is not installed. Install dependencies with: pip install -r requirements.txt"
        )

    try:
        _render_with_mmdc(source, svg_path)
        _render_with_mmdc(source, png_path)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        if _looks_like_missing_browser_error(stderr):
            try:
                _ensure_playwright_chromium()
                _render_with_mmdc(source, svg_path)
                _render_with_mmdc(source, png_path)
                return [svg_path, png_path]
            except subprocess.CalledProcessError as retry_exc:
                retry_stderr = (retry_exc.stderr or "").strip()
                raise RuntimeError(
                    "Failed to render Mermaid diagram after auto-installing Chromium: "
                    f"{retry_stderr}"
                ) from retry_exc

        raise RuntimeError(f"Failed to render Mermaid diagram: {stderr}") from exc

    return [svg_path, png_path]
