# Evaluation Plan and Results Template

Use this file as a draft for the final project writeup or presentation notes.

## Evaluation 1: Human Questionnaire for Onboarding Usefulness

### Goal

Measure whether a human evaluator can understand the repository from the
generated architecture diagram alone.

### Setup

- Artifact evaluated: `aai/output_analysis/06_visual/mermaid_draft.mmd`
- Artifact evaluated: `aai/output_analysis/06_visual/mermaid_refined.mmd`
- Human questionnaire: `aai/evaluation/human_questionnaire.md`
- Raters: 4 group members
- Evaluator constraint: ratings must be based on the diagram only

### Method

1. Give each rater the draft and refined diagrams.
2. Have each rater fill out the questionnaire independently.
3. Compute the average score for:
   - Onboarding usefulness: Q1-Q10
   - Correctness and trust: Q11-Q15
   - Overall score: Q1-Q15
4. Compare average draft versus refined scores.
5. Summarize open-ended responses for recurring themes.

### Table Template

| Metric | Draft Average | Refined Average | Notes |
|--------|---------------|-----------------|-------|
| Q1-Q10 Onboarding Usefulness |  |  |  |
| Q11-Q15 Correctness and Trust |  |  |  |
| Q1-Q15 Overall Score |  |  |  |

### Suggested Summary Sentence

The refined diagram received higher human ratings for onboarding usefulness than
the draft, suggesting that the critique-and-revision loop improved clarity,
component organization, and interpretability.

## Evaluation 2: Code-Grounded Architecture Correctness

### Goal

Measure whether the generated diagram accurately reflects the actual codebase.

### Setup

- Source of truth: repository code and project documentation
- Evaluated artifacts:
  - `aai/output_analysis/06_visual/mermaid_draft.mmd`
  - `aai/output_analysis/06_visual/mermaid_refined.mmd`

### Method

1. Select 5-10 concrete architecture facts from the real codebase.
2. Check whether each fact is represented correctly in the draft and refined diagrams.
3. Score each fact as:
   - `Correct`
   - `Partially Correct`
   - `Unsupported`
   - `Incorrect`

### Good Fact Types

- The true entry point or top-level orchestrator
- A major subsystem boundary
- A key dependency between two components
- An external service or file dependency
- A critical data flow
- A design pattern visible in code
- A concurrency, event, or observer relationship

### Table Template

| Fact ID | Ground-Truth Fact | Draft Score | Refined Score | Evidence in Code | Notes |
|---------|-------------------|-------------|---------------|------------------|-------|
| F1 |  |  |  |  |  |
| F2 |  |  |  |  |  |
| F3 |  |  |  |  |  |
| F4 |  |  |  |  |  |
| F5 |  |  |  |  |  |

### Suggested Summary Sentence

The refined diagram was more accurate than the draft on core architectural
facts, especially around central components, key dependencies, and system
boundaries.

## Results

### Quantitative Results

Fill in the final numbers:

- Draft human onboarding score: `__ / 5`
- Refined human onboarding score: `__ / 5`
- Draft human correctness and trust score: `__ / 5`
- Refined human correctness and trust score: `__ / 5`
- Draft overall questionnaire score: `__ / 5`
- Refined overall questionnaire score: `__ / 5`
- Draft correctness facts marked correct or partially correct: `__ / __`
- Refined correctness facts marked correct or partially correct: `__ / __`

### Qualitative Results

Use a short paragraph like this:

The critique-and-revision loop improved the usefulness of the generated
architecture output. Human raters scored the refined diagram higher than the
draft for onboarding usefulness and trustworthiness, and the refined diagram
also aligned better with code-grounded architectural facts. However, some
runtime behavior and implementation details still required direct code inspection.

## Limitations

- The human questionnaire depends on rater judgment and consistency.
- Diagram-only evaluation cannot recover details that were never inferred.
- Some architectural properties are easier to verify from code than from diagrams.
- Results may vary across repositories with different structures and naming quality.

## Final Takeaway

This project demonstrates that a staged multi-agent pipeline can generate useful
architecture diagrams for onboarding, and that a critique-and-revision loop can
improve both clarity and architectural fidelity relative to a first-pass draft.
