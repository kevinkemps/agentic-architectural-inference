"""Evaluation runner for pipeline quality assessment.

Compares pipeline outputs before and after critic strategy evolution.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from lib.agents import CritiqueEvaluator, STAGES
from lib.logging_config import get_logger

logger = get_logger(__name__)


def run_evaluation(
    output_dir: Path,
    eval_questions_path: Path,
    comparison_mode: bool = False,
) -> dict:
    """Evaluate a pipeline run using evaluation questions.
    
    Args:
        output_dir: Root output directory from pipeline run
        eval_questions_path: Path to evaluation questions markdown
        comparison_mode: If True, compare against prior run
        
    Returns:
        Dict with evaluation metrics and results
    """
    logger.info(f"Starting evaluation with output_dir={output_dir}, comparison_mode={comparison_mode}")
    
    try:
        evaluator = CritiqueEvaluator(output_dir=output_dir)
        logger.debug("CritiqueEvaluator initialized")
    except Exception as exc:
        logger.error(f"Failed to initialize CritiqueEvaluator: {exc}", exc_info=True)
        return {}
    
    try:
        evaluator.load_eval_questions(eval_questions_path)
        logger.debug(f"Loaded evaluation questions from {eval_questions_path}")
    except Exception as exc:
        logger.error(f"Failed to load evaluation questions: {exc}", exc_info=True)
        return {}

    try:
        results = evaluator.evaluate()
        logger.debug(f"Evaluation complete, results keys: {list(results.keys())}")
    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}", exc_info=True)
        return {}
    
    # Load feedback to compute aggregate metrics
    try:
        feedback = evaluator.load_feedback()
        logger.debug(f"Loaded feedback with {len(feedback)} entries")
    except Exception as exc:
        logger.error(f"Failed to load feedback: {exc}", exc_info=True)
        feedback = {}
    
    # Compute summary statistics
    if feedback:
        try:
            effectiveness_scores = [run.get("effectiveness_score", 0) for run in feedback.values()]
            false_positive_risks = [run.get("false_positive_risk", 0) for run in feedback.values()]
            actionability_scores = [run.get("actionability_score", 0) for run in feedback.values()]
            
            logger.debug(f"Computing averages from {len(feedback)} runs")
            
            summary = {
                "total_runs": len(feedback),
                "avg_effectiveness": round(sum(effectiveness_scores) / len(effectiveness_scores), 1) if effectiveness_scores else 0,
                "avg_false_positive_risk": round(sum(false_positive_risks) / len(false_positive_risks), 1) if false_positive_risks else 0,
                "avg_actionability": round(sum(actionability_scores) / len(actionability_scores), 1) if actionability_scores else 0,
            }
            logger.info(f"Summary computed: avg_effectiveness={summary['avg_effectiveness']}%, avg_false_positive_risk={summary['avg_false_positive_risk']}%, avg_actionability={summary['avg_actionability']}%")
        except Exception as exc:
            logger.error(f"Failed to compute summary statistics: {exc}", exc_info=True)
            summary = {
                "total_runs": len(feedback),
                "avg_effectiveness": 0,
                "avg_false_positive_risk": 0,
                "avg_actionability": 0,
            }
    else:
        logger.info("No feedback found, using zero values")
        summary = {
            "total_runs": 0,
            "avg_effectiveness": 0,
            "avg_false_positive_risk": 0,
            "avg_actionability": 0,
        }

    return {
        "latest_result": results,
        "summary": summary,
        "feedback_count": len(feedback),
    }


def save_metrics(output_dir: Path, metrics: dict) -> None:
    """Save evaluation metrics to metrics_summary.md."""
    try:
        metrics_file = output_dir / "evaluation" / "metrics_summary.md"
        metrics_file.parent.mkdir(parents=True, exist_ok=True)

        content = f"""# Evaluation Metrics Summary

## Latest Run
- Effectiveness Score: {metrics['latest_result'].get('effectiveness_score', 0)}%
- False Positive Risk: {metrics['latest_result'].get('false_positive_risk', 0)}%
- Actionability Score: {metrics['latest_result'].get('actionability_score', 0)}%

## Aggregate Statistics ({metrics['summary']['total_runs']} runs)
- Average Effectiveness: {metrics['summary']['avg_effectiveness']}%
- Average False Positive Risk: {metrics['summary']['avg_false_positive_risk']}%
- Average Actionability: {metrics['summary']['avg_actionability']}%

## Coverage
- Evaluation Questions Covered: {len(metrics['latest_result'].get('coverage', []))} 
  (Run IDs: {metrics['latest_result'].get('coverage', [])})
"""

        metrics_file.write_text(content, encoding="utf-8")
        logger.info(f"Metrics saved to {metrics_file}")
    except Exception as exc:
        logger.error(f"Failed to save metrics: {exc}", exc_info=True)


def main() -> None:
    """Run evaluation on current output directory."""
    import argparse
    from lib.logging_config import configure_logging
    
    logger.info("Starting evaluation runner")
    parser = argparse.ArgumentParser(description="Evaluate pipeline output")
    parser.add_argument("--out-dir", default="output_analysis", help="Pipeline output directory")
    parser.add_argument("--eval-questions", default="../aai/evaluation/eval_questions.md", help="Path to eval questions")
    
    args = parser.parse_args()
    logger.debug(f"Arguments parsed: out_dir={args.out_dir}, eval_questions={args.eval_questions}")
    
    output_dir = Path(args.out_dir)
    eval_questions = Path(args.eval_questions)
    logger.debug(f"Resolved paths: output_dir={output_dir.absolute()}, eval_questions={eval_questions.absolute()}")
    
    try:
        if not eval_questions.exists():
            error_msg = f"Evaluation questions not found at {eval_questions}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        logger.debug("✓ Evaluation questions file exists")
        
        if not output_dir.exists():
            error_msg = f"Output directory not found at {output_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        logger.debug("✓ Output directory exists")
        
        logger.info("Calling run_evaluation...")
        metrics = run_evaluation(output_dir, eval_questions)
        logger.info("run_evaluation returned successfully")
        
        logger.info("Saving metrics...")
        save_metrics(output_dir, metrics)
        
        # Print summary to stdout for user feedback
        print("\n=== Evaluation Results ===")
        print(f"Effectiveness: {metrics['summary']['avg_effectiveness']}%")
        print(f"False Positive Risk: {metrics['summary']['avg_false_positive_risk']}%")
        print(f"Actionability: {metrics['summary']['avg_actionability']}%")
        print(f"\n✓ Evaluation complete. Metrics saved to {output_dir / 'evaluation' / 'metrics_summary.md')")
        logger.info("Evaluation completed successfully")
    
    except FileNotFoundError as exc:
        logger.error(f"FileNotFoundError: {exc}", exc_info=True)
        raise SystemExit(1) from exc
    except json.JSONDecodeError as exc:
        logger.error(f"JSONDecodeError parsing feedback: {exc}", exc_info=True)
        raise SystemExit(1) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during evaluation: {exc}", exc_info=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
