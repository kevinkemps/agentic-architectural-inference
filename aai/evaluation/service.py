from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

if __package__:
    from ..lib.prompts import (
        EVALUATION_DIAGRAM_PROMPT,
        EVALUATION_JUDGE_PROMPT,
        EVALUATION_QUESTION_GENERATOR_PROMPT,
        EVALUATION_REPO_PROMPT,
    )
    from ..lib.repo_reader import load_readme, load_repo_files
else:  # pragma: no cover - supports running from inside aai/
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

    digest_parts = []
    if readme:
        digest_parts.append(f"## README\n{readme[:6000]}")

    file_list = "\n".join(f"- {source.path}" for source in files)
    digest_parts.append(f"## Sampled Files\n{file_list}")

    for source in files:
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


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise RuntimeError("LLM response did not contain JSON.")
        return json.loads(match.group(0))


def _invoke_json(llm, system_prompt: str, human_content: str) -> tuple[dict, TokenStats]:
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]
    )
    return _extract_json(response.content), _usage_from_response(response)


def generate_repo_specific_questions(
    *,
    repo_digest: str,
    core_questions: list[str],
    llm,
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
) -> EvaluationResult:
    core_questions = load_questions(questions_path)
    repo_digest = build_repo_digest(repo_path)
    repo_specific_questions, question_usage = generate_repo_specific_questions(
        repo_digest=repo_digest,
        core_questions=core_questions,
        llm=llm,
    )
    questions = [*core_questions, *repo_specific_questions]
    question_block = "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))

    repo_payload, repo_usage = _invoke_json(
        llm,
        EVALUATION_REPO_PROMPT,
        f"## Questions\n{question_block}\n\n## Repository Digest\n{repo_digest}",
    )
    diagram_payload, diagram_usage = _invoke_json(
        llm,
        EVALUATION_DIAGRAM_PROMPT,
        f"## Questions\n{question_block}\n\n## Mermaid Diagram\n{diagram_text}",
    )
    judge_payload, judge_usage = _invoke_json(
        llm,
        EVALUATION_JUDGE_PROMPT,
        (
            f"## Questions\n{question_block}\n\n"
            f"## Repository Answers\n{json.dumps(repo_payload, indent=2)}\n\n"
            f"## Diagram Answers\n{json.dumps(diagram_payload, indent=2)}"
        ),
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
