from __future__ import annotations
import argparse
from .pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "aai2 – multi-agent architecture inference pipeline.\n"
            "Stages: 01_scout → 02_aggregate → 03_draft → 04_critique → 05_refined → 06_visual"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # --- Required / primary ---
    parser.add_argument(
        "--repo-path",
        default="./code_base",
        help="Path to the repository to analyse (default: current directory)",
    )

    # --- Output ---
    parser.add_argument(
        "--out-dir",
        default="output_analysis",
        help="Root output directory; stage sub-dirs are created automatically (default: output_analysis)",
    )

    # --- Chunking / context ---
    parser.add_argument(
        "--max-chars-per-chunk",
        type=int,
        default=50_000,
        help=(
            "Maximum characters per file chunk sent to the FileSummarizer LLM.  "
            "~50 000 for a 4-bit 8B local model; ~500 000 for gpt-4o (default: 50000)"
        ),
    )

    parser.add_argument(
        "--architect-threshold",
        type=int,
        default=20_000,
        help="Maximum total characters the ContextManager passes to the Architect (default: 20000)",
    )

    # --- Critic loop ---
    parser.add_argument(
        "--critic-rounds",
        type=int,
        default=1,
        help="Number of critique → revision cycles (default: 1)",
    )

    # --- Optional reference architecture ---
    parser.add_argument(
        "--arch-md-path",
        default=None,
        help="Optional path to an external reference architecture .md file",
    )

    # --- Verbosity ---
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress logging",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        out_path = run_pipeline(
            repo_path=args.repo_path,
            out_dir=args.out_dir,
            arch_md_path=args.arch_md_path,
            max_chars_per_chunk=args.max_chars_per_chunk,
            architect_threshold=args.architect_threshold,
            critic_rounds=args.critic_rounds,
            verbose=not args.quiet,
        )
        print(f"\nOutput directory: {out_path}")
        print(f"  Draft diagram  : {out_path / '03_draft' / 'mermaid.md'}")
        print(f"  Refined diagram: {out_path / '05_refined' / 'mermaid.md'}")
    except RuntimeError as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()
