from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

try:
    from ..lib.prompts import (
        EVALUATION_DIAGRAM_PROMPT,
        EVALUATION_JUDGE_PROMPT,
        EVALUATION_QUESTION_GENERATOR_PROMPT,
        EVALUATION_REPO_PROMPT,
    )
    from ..lib.repo_reader import load_readme, load_repo_files
except ImportError:  # pragma: no cover - supports running from inside aai/
    from lib.prompts import (  # type: ignore[no-redef]
        EVALUATION_DIAGRAM_PROMPT,
        EVALUATION_JUDGE_PROMPT,
        EVALUATION_QUESTION_GENERATOR_PROMPT,
        EVALUATION_REPO_PROMPT,
    )
    from lib.repo_reader import load_readme, load_repo_files  # type: ignore[no-redef]


@dataclass
class TokenStats:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class EvaluationResult:
    questions: list[dict]
    overall_score: float
    summary: str
    core_questions: list[str]
    repo_specific_questions: list[str]
    repo_answers: list[dict]
    diagram_answers: list[dict]
    token_stats: TokenStats

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["overall_score"] = round(self.overall_score, 2)
        return payload


def load_questions(questions_path: str | Path | None = None) -> list[str]:
    path = Path(questions_path) if questions_path else Path(__file__).with_name("eval_questions.md")
    text = path.read_text(encoding="utf-8")
    questions: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*\d+\.\s+(.*\S)\s*$", line)
        if match:
            questions.append(match.group(1))
    if not questions:
        raise RuntimeError(f"No numbered evaluation questions found in {path}")
    return questions


def _write_question_markdown(path: Path, title: str, questions: list[str]) -> None:
    lines = [f"# {title}", ""]
    lines.extend(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_numbered_questions(text: str) -> list[str]:
    questions: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*\d+\.\s+(.*\S)\s*$", line)
        if match:
            questions.append(match.group(1))
    return questions


def _load_reused_repo_specific_questions(
    *,
    shared_group_root: str | Path | None,
    current_run_output_dir: str | Path | None,
) -> list[str] | None:
    if shared_group_root is None:
        return None

    group_root = Path(shared_group_root)
    if not group_root.exists() or not group_root.is_dir():
        return None

    current_output = Path(current_run_output_dir).resolve() if current_run_output_dir else None
    candidates = sorted(group_root.glob("*/evaluation/repo_specific_eval_questions.md"))

    for candidate in candidates:
        run_output_dir = candidate.parent.parent.resolve()
        if current_output is not None and run_output_dir == current_output:
            continue
        parsed = _parse_numbered_questions(candidate.read_text(encoding="utf-8"))
        if len(parsed) >= 5:
            return parsed

    return None


def build_repo_digest(
    repo_path: str | Path,
    *,
    max_files: int = 40,
    max_chars_per_file: int = 2500,
) -> str:
    readme = load_readme(repo_path).strip()
    files = load_repo_files(
        repo_path,
        max_files=max_files,
        max_chars_per_file=max_chars_per_file,
    )
    non_notebook_files = [source for source in files if not source.path.lower().endswith(".ipynb")]

    digest_parts = []
    if readme:
        digest_parts.append(f"## README\n{readme[:6000]}")

    if non_notebook_files:
        file_list = "\n".join(f"- {source.path}" for source in non_notebook_files)
    else:
        file_list = "- (no non-notebook files were sampled for evaluation digest)"
    digest_parts.append(f"## Sampled Files\n{file_list}")

    for source in non_notebook_files:
        digest_parts.append(f"## FILE: {source.path}\n{source.content}")

    return "\n\n".join(digest_parts)


def _usage_from_response(response) -> TokenStats:
    usage = getattr(response, "usage_metadata", None) or {}
    return TokenStats(
        input_tokens=int(usage.get("input_tokens", 0) or 0),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
        total_tokens=int(usage.get("total_tokens", 0) or 0),
    )


def _add_usage(left: TokenStats, right: TokenStats) -> TokenStats:
    return TokenStats(
        input_tokens=left.input_tokens + right.input_tokens,
        output_tokens=left.output_tokens + right.output_tokens,
        total_tokens=left.total_tokens + right.total_tokens,
    )


def _raw_response_debug_dir(output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        return Path(output_dir) / "debug_raw_responses"
    return Path("/tmp") / "aai_eval_debug" / uuid.uuid4().hex


def _response_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _write_raw_response(*, debug_dir: Path, step_name: str, raw_text: str) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / f"{step_name}.raw.txt").write_text(raw_text, encoding="utf-8")


def _extract_json(text: str, *, step_name: str) -> dict:
    parse_errors: list[json.JSONDecodeError] = []

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        parse_errors.append(exc)

    for match in re.finditer(r"```json\s*(\{.*?\})\s*```", text, re.IGNORECASE | re.DOTALL):
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            parse_errors.append(exc)

    for match in re.finditer(r"\{.*?\}", text, re.DOTALL):
        candidate = match.group(0).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            parse_errors.append(exc)

    message = (
        f"Failed to parse JSON for evaluation step '{step_name}'. "
        "Tried strict JSON, fenced json blocks, and object extraction."
    )
    if parse_errors:
        raise RuntimeError(message) from parse_errors[-1]
    raise RuntimeError(message)


def _invoke_json(
    llm,
    system_prompt: str,
    human_content: str,
    *,
    step_name: str,
    debug_dir: Path,
) -> tuple[dict, TokenStats]:
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]
    )
    raw_text = _response_text(getattr(response, "content", ""))
    _write_raw_response(debug_dir=debug_dir, step_name=step_name, raw_text=raw_text)
    return _extract_json(raw_text, step_name=step_name), _usage_from_response(response)


def generate_repo_specific_questions(
    *,
    repo_digest: str,
    core_questions: list[str],
    llm,
    debug_dir: Path,
) -> tuple[list[str], TokenStats]:
    core_question_block = "\n".join(
        f"{index}. {question}" for index, question in enumerate(core_questions, start=1)
    )
    payload, usage = _invoke_json(
        llm,
        EVALUATION_QUESTION_GENERATOR_PROMPT,
        (
            f"## Fixed Core Questions\n{core_question_block}\n\n"
            f"## Repository Digest\n{repo_digest}"
        ),
        step_name="question_generator",
        debug_dir=debug_dir,
    )
    raw_questions = payload.get("questions", [])
    cleaned_questions: list[str] = []
    seen: set[str] = set(question.strip().lower() for question in core_questions)

    for item in raw_questions:
        question = str(item).strip()
        if not question:
            continue
        normalized = question.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned_questions.append(question)
        if len(cleaned_questions) == 10:
            break

    if len(cleaned_questions) < 5:
        raise RuntimeError("Question generator returned fewer than 5 usable repo-specific questions.")

    return cleaned_questions, usage


def evaluate_diagram(
    *,
    repo_path: str | Path,
    diagram_text: str,
    llm,
    questions_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    shared_evaluation_group_dir: str | Path | None = None,
) -> EvaluationResult:
    core_questions = load_questions(questions_path)
    repo_digest = build_repo_digest(repo_path)
    debug_dir = _raw_response_debug_dir(output_dir)
    current_run_output_dir = Path(output_dir).parent if output_dir is not None else None
    repo_specific_questions = _load_reused_repo_specific_questions(
        shared_group_root=shared_evaluation_group_dir,
        current_run_output_dir=current_run_output_dir,
    )
    if repo_specific_questions is None:
        repo_specific_questions, question_usage = generate_repo_specific_questions(
            repo_digest=repo_digest,
            core_questions=core_questions,
            llm=llm,
            debug_dir=debug_dir,
        )
    else:
        question_usage = TokenStats()
    questions = [*core_questions, *repo_specific_questions]
    question_block = "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))

    repo_payload, repo_usage = _invoke_json(
        llm,
        EVALUATION_REPO_PROMPT,
        f"## Questions\n{question_block}\n\n## Repository Digest\n{repo_digest}",
        step_name="repo_answers",
        debug_dir=debug_dir,
    )
    diagram_payload, diagram_usage = _invoke_json(
        llm,
        EVALUATION_DIAGRAM_PROMPT,
        f"## Questions\n{question_block}\n\n## Mermaid Diagram\n{diagram_text}",
        step_name="diagram_answers",
        debug_dir=debug_dir,
    )
    judge_payload, judge_usage = _invoke_json(
        llm,
        EVALUATION_JUDGE_PROMPT,
        (
            f"## Questions\n{question_block}\n\n"
            f"## Repository Answers\n{json.dumps(repo_payload, indent=2)}\n\n"
            f"## Diagram Answers\n{json.dumps(diagram_payload, indent=2)}"
        ),
        step_name="judge",
        debug_dir=debug_dir,
    )

    question_scores = judge_payload.get("questions", [])
    if not question_scores:
        raise RuntimeError("Evaluation judge returned no question scores.")

    total_score = sum(int(item.get("score", 0) or 0) for item in question_scores)
    overall_score = (total_score / (len(question_scores) * 5)) * 100
    usage_totals = _add_usage(
        _add_usage(_add_usage(question_usage, repo_usage), diagram_usage),
        judge_usage,
    )

    result = EvaluationResult(
        questions=question_scores,
        overall_score=overall_score,
        summary=str(judge_payload.get("summary", "")).strip(),
        core_questions=core_questions,
        repo_specific_questions=repo_specific_questions,
        repo_answers=repo_payload.get("answers", []),
        diagram_answers=diagram_payload.get("answers", []),
        token_stats=usage_totals,
    )

    if output_dir is not None:
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        _write_question_markdown(
            destination / "core_eval_questions.md",
            "Core Evaluation Questions",
            core_questions,
        )
        _write_question_markdown(
            destination / "repo_specific_eval_questions.md",
            "Repo-Specific Evaluation Questions",
            repo_specific_questions,
        )
        _write_question_markdown(
            destination / "combined_eval_questions.md",
            "Combined Evaluation Questions",
            questions,
        )
        (destination / "repo_answers.json").write_text(
            json.dumps(repo_payload, indent=2),
            encoding="utf-8",
        )
        (destination / "diagram_answers.json").write_text(
            json.dumps(diagram_payload, indent=2),
            encoding="utf-8",
        )
        (destination / "scorecard.json").write_text(
            json.dumps(result.to_dict(), indent=2),
            encoding="utf-8",
        )

    return result
