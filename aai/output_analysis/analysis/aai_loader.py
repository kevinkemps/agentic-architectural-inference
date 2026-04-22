"""Loader/normalizer for AAI run outputs.

Parses every ``<timestamp>_debug_compare/debug_analysis.json`` under a runs
directory and returns long-form pandas DataFrames suitable for trend and
framework-comparison analysis.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd


# ---------------------------------------------------------------------------
# Framework label derivation
# ---------------------------------------------------------------------------

def _framework_label(mode: str | None, used_critic: bool | None) -> str:
    """Map (mode, used_critic) -> stable framework name."""
    if mode == "single_prompt":
        return "Single Shot"
    if mode == "multi_agent" and used_critic:
        return "Critic On"
    if mode == "multi_agent":
        return "Critic Off"
    return f"Unknown ({mode}, critic={used_critic})"


_WS_RE = re.compile(r"\s+")


def _normalize_question(text: str) -> str:
    """Lowercase + collapse whitespace for grouping."""
    if text is None:
        return ""
    return _WS_RE.sub(" ", text.strip().lower())


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

@dataclass
class _ParsedRun:
    runs_rows: list[dict]
    stages_rows: list[dict]
    questions_rows: list[dict]


def _parse_debug_analysis(path: Path) -> _ParsedRun:
    """Parse a single debug_analysis.json into row dicts for the 3 DFs."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    run_id = path.parent.name
    generated_at = pd.to_datetime(data.get("generated_at"), errors="coerce")

    runs_rows: list[dict] = []
    stages_rows: list[dict] = []
    questions_rows: list[dict] = []

    for entry in data.get("runs", []):
        pipeline = entry.get("pipeline", {}) or {}
        evaluation = entry.get("evaluation", {}) or {}

        mode = pipeline.get("mode")
        used_critic = pipeline.get("used_critic")
        framework = _framework_label(mode, used_critic)

        total_tokens = pipeline.get("total_tokens", {}) or {}
        questions = evaluation.get("questions", []) or []
        core_questions = evaluation.get("core_questions", []) or []
        core_norm = {_normalize_question(q) for q in core_questions}

        n_questions = len(questions)
        n_core = sum(
            1 for q in questions if _normalize_question(q.get("question", "")) in core_norm
        )

        runs_rows.append(
            {
                "run_id": run_id,
                "generated_at": generated_at,
                "framework": framework,
                "label": entry.get("label"),
                "mode": mode,
                "used_critic": used_critic,
                "overall_score": evaluation.get("overall_score"),
                "core_overall_score": evaluation.get("core_overall_score"),
                "total_duration_seconds": pipeline.get("total_duration_seconds"),
                "input_tokens": total_tokens.get("input_tokens"),
                "output_tokens": total_tokens.get("output_tokens"),
                "total_tokens": total_tokens.get("total_tokens"),
                "n_questions": n_questions,
                "n_core_questions": n_core,
                "n_variation_questions": n_questions - n_core,
                "summary": evaluation.get("summary"),
            }
        )

        for stage in pipeline.get("stage_stats", []) or []:
            tok = stage.get("tokens", {}) or {}
            stages_rows.append(
                {
                    "run_id": run_id,
                    "generated_at": generated_at,
                    "framework": framework,
                    "stage": stage.get("stage"),
                    "duration_seconds": stage.get("duration_seconds"),
                    "input_tokens": tok.get("input_tokens"),
                    "output_tokens": tok.get("output_tokens"),
                    "total_tokens": tok.get("total_tokens"),
                }
            )

        for idx, q in enumerate(questions):
            q_text = q.get("question", "")
            q_norm = _normalize_question(q_text)
            questions_rows.append(
                {
                    "run_id": run_id,
                    "generated_at": generated_at,
                    "framework": framework,
                    "question_index": idx,
                    "question": q_text,
                    "question_norm": q_norm,
                    "score": q.get("score"),
                    "rationale": q.get("rationale"),
                    "is_core": q_norm in core_norm,
                }
            )

    return _ParsedRun(runs_rows, stages_rows, questions_rows)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _iter_debug_analysis_paths(runs_dir: Path) -> Iterable[Path]:
    for child in sorted(runs_dir.iterdir()):
        if child.is_dir() and child.name.endswith("_debug_compare"):
            candidate = child / "debug_analysis.json"
            if candidate.exists():
                yield candidate


@lru_cache(maxsize=8)
def _load_all_cached(runs_dir_str: str) -> tuple[pd.DataFrame, ...]:
    runs_dir = Path(runs_dir_str)
    if not runs_dir.exists():
        raise FileNotFoundError(f"runs_dir does not exist: {runs_dir}")

    all_runs: list[dict] = []
    all_stages: list[dict] = []
    all_questions: list[dict] = []

    for path in _iter_debug_analysis_paths(runs_dir):
        parsed = _parse_debug_analysis(path)
        all_runs.extend(parsed.runs_rows)
        all_stages.extend(parsed.stages_rows)
        all_questions.extend(parsed.questions_rows)

    runs_df = pd.DataFrame(all_runs)
    stages_df = pd.DataFrame(all_stages)
    questions_df = pd.DataFrame(all_questions)

    # Stable sorting for downstream plots.
    if not runs_df.empty:
        runs_df = runs_df.sort_values(["generated_at", "framework"]).reset_index(
            drop=True
        )
    if not stages_df.empty:
        stages_df = stages_df.sort_values(
            ["generated_at", "framework", "stage"]
        ).reset_index(drop=True)
    if not questions_df.empty:
        questions_df = questions_df.sort_values(
            ["generated_at", "framework", "question_index"]
        ).reset_index(drop=True)

    return runs_df, stages_df, questions_df


def load_all(
    runs_dir: str | Path,
    repo_name: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and normalize all AAI run data under ``runs_dir``.

    Parameters
    ----------
    runs_dir
        Parent folder containing ``*_debug_compare/`` subfolders.
    repo_name
        Optional human-friendly repo label. When provided, a ``repo`` column
        is stamped onto every returned DataFrame. The original absolute repo
        path from ``debug_analysis.json`` is intentionally not stored.

    Returns
    -------
    (runs_df, stages_df, questions_df)
        Long-form DataFrames. ``runs_df`` has one row per
        (run_folder, framework). ``questions_df`` has one row per question
        with ``is_core`` flag.
    """
    runs_df, stages_df, questions_df = _load_all_cached(
        str(Path(runs_dir).resolve())
    )
    # Return defensive copies so notebook mutations cannot poison the cache.
    runs_df = runs_df.copy()
    stages_df = stages_df.copy()
    questions_df = questions_df.copy()
    if repo_name:
        for df in (runs_df, stages_df, questions_df):
            df.insert(0, "repo", repo_name)
    return runs_df, stages_df, questions_df


def infer_repo_name(runs_dir: str | Path) -> str | None:
    """(Legacy) Peek at the first ``debug_analysis.json`` to derive the repo
    basename. Prefer setting ``REPO_NAME`` explicitly and passing it to
    :func:`load_all` instead &mdash; the absolute repo path is not stored on
    the returned DataFrames.
    """
    runs_dir = Path(runs_dir)
    for path in _iter_debug_analysis_paths(runs_dir):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        repo_path = data.get("repo_path")
        if repo_path:
            return Path(repo_path).name
    return None


FRAMEWORK_ORDER = ["Single Shot", "Critic Off", "Critic On"]
FRAMEWORK_COLORS = {
    "Single Shot": "#4C78A8",
    "Critic Off": "#F58518",
    "Critic On": "#54A24B",
}
