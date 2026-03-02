"""CLI entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline, write_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-agent architecture inference with critic loop."
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI model name",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=120,
        help="Maximum number of source files to scan",
    )
    parser.add_argument(
        "--max-chars-per-file",
        type=int,
        default=8000,
        help="Maximum chars loaded per file",
    )
    parser.add_argument(
        "--critic-rounds",
        type=int,
        default=2,
        help="Number of architect<->critic refinement rounds",
    )
    parser.add_argument(
        "--out-dir",
        default="outputs/latest",
        help="Output directory for mermaid + reports",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable progress logging during the run",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        artifacts = run_pipeline(
            repo_path=args.repo_path,
            model=args.model,
            max_files=args.max_files,
            max_chars_per_file=args.max_chars_per_file,
            critic_rounds=args.critic_rounds,
            verbose=not args.quiet,
        )
        write_artifacts(args.out_dir, artifacts)
        out_path = Path(args.out_dir).resolve()
        print(f"Done. Mermaid diagram: {out_path / 'architecture.mmd'}")
        print(f"Critic report: {out_path / 'critic_report.md'}")
        run_stats = artifacts.run_stats
        llm_stats = run_stats.get("llm", {})
        print(
            "Run stats: "
            f"runtime={run_stats.get('runtime_seconds', 0)}s, "
            f"requests={llm_stats.get('requests', 0)}, "
            f"tokens={llm_stats.get('total_tokens', 0)}"
        )
    except RuntimeError as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()
