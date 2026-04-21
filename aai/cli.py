from __future__ import annotations

import argparse

if __package__:
    from .pipeline import run_pipeline_with_details
else:  # pragma: no cover - supports running from inside aai/
    from pipeline import run_pipeline_with_details  # type: ignore[no-redef]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "aai architecture inference runner.\n"
            "Modes: multi_agent (default) or single_prompt."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo-path",
        default="./code_base",
        help="Path to the repository to analyse.",
    )
    parser.add_argument(
        "--out-dir",
        default="output_analysis",
        help="Root output directory; stage sub-dirs are cleared and recreated automatically.",
    )
    parser.add_argument(
        "--mode",
        choices=["multi_agent", "single_prompt"],
        default="multi_agent",
        help="Generation mode to run.",
    )
    parser.add_argument(
        "--max-chars-per-chunk",
        type=int,
        default=50_000,
        help="Maximum characters per file chunk sent to the FileSummarizer LLM.",
    )
    parser.add_argument(
        "--architect-threshold",
        type=int,
        default=20_000,
        help="Maximum total characters the ContextManager passes to the Architect.",
    )
    parser.add_argument(
        "--critic-rounds",
        type=int,
        default=1,
        help="Number of critique → revision cycles to run. Use 0 to disable the critic.",
    )
    parser.add_argument(
        "--arch-md-path",
        default=None,
        help="Optional path to an external reference architecture .md file.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress logging.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = run_pipeline_with_details(
            repo_path=args.repo_path,
            out_dir=args.out_dir,
            arch_md_path=args.arch_md_path,
            max_chars_per_chunk=args.max_chars_per_chunk,
            architect_threshold=args.architect_threshold,
            critic_rounds=args.critic_rounds,
            verbose=not args.quiet,
            mode=args.mode,
        )
        print(f"\nOutput directory: {result.output_dir}")
        print(f"  Draft diagram   : {result.draft_diagram_path}")
        print(f"  Refined diagram : {result.refined_diagram_path}")
        print(f"  Selected diagram: {result.selected_diagram_path}")
        print(f"  Total time      : {result.total_duration_seconds:.2f}s")
        print(f"  Total tokens    : {result.total_tokens.total_tokens}")
    except RuntimeError as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()
