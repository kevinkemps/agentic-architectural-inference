"""Repository scanning helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".java",
    ".kt",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".scala",
    ".sql",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".sh",
}

SKIP_DIRS = {
    ".git",
    ".next",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "target",
    "__pycache__",
}


@dataclass
class SourceFile:
    path: str
    content: str


def _looks_text(data: bytes) -> bool:
    return b"\x00" not in data


def load_repo_files(
    repo_path: str | Path,
    max_files: int = 120,
    max_chars_per_file: int = 8000,
) -> list[SourceFile]:
    root = Path(repo_path).resolve()
    files: list[SourceFile] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if len(files) >= max_files:
                return files
            path = Path(dirpath) / filename
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                raw = path.read_bytes()[: max_chars_per_file * 2]
                if not _looks_text(raw):
                    continue
                text = raw.decode("utf-8", errors="replace")[:max_chars_per_file]
            except OSError:
                continue
            files.append(SourceFile(path=str(path.relative_to(root)), content=text))

    return files


def load_readme(repo_path: str | Path) -> str:
    root = Path(repo_path).resolve()
    candidates = [root / "README.md", root / "readme.md", root / "README"]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="replace")
    return ""
