# Human Evaluation Questionnaire

Use this questionnaire with human evaluators to judge the quality of generated
architecture diagrams. It is designed for side-by-side rating of draft and
refined diagrams by multiple raters.

## Instructions for Raters

You will evaluate one or two generated architecture diagrams for the same
repository.

- If comparing two diagrams, evaluate both the `draft` and `refined` versions.
- Base your answers only on the diagram and any evaluation instructions provided.
- If you are unsure, choose the lower score.
- Use the same scale consistently across all questions.

## Rating Scale

Use a 1 to 5 score for each item:

- `1` = Strongly Disagree
- `2` = Disagree
- `3` = Neutral / Partially
- `4` = Agree
- `5` = Strongly Agree

## Section A: Onboarding Usefulness

Rate each statement for the diagram you are reviewing.

1. I can understand the overall purpose of the repository from this diagram.
2. I can identify the most likely entry point or top-level orchestrator.
3. I can follow the main execution flow shown by the diagram.
4. The major components or subsystems are clearly represented.
5. External dependencies or inputs are visible and understandable.
6. Outputs, side effects, or downstream artifacts are visible and understandable.
7. The most important or central components are easy to identify.
8. The diagram helps me identify potentially fragile or high-risk parts of the system.
9. The relationships and arrows are clear enough to support architectural reasoning.
10. The diagram would be useful for onboarding a new engineer to this repository.

## Section B: Correctness and Trust

Rate each statement for the diagram you are reviewing.

11. The diagram appears internally consistent.
12. The component names and boundaries look plausible for the repository.
13. The edges and dependencies appear believable rather than speculative.
14. I would trust this diagram as a starting point for codebase exploration.
15. The diagram avoids unsupported or confusing architectural claims.

## Section C: Open-Ended Questions

Answer briefly.

1. What part of the diagram was most helpful?
2. What part of the diagram was most confusing or least trustworthy?
3. What important information seems missing?
4. If comparing draft and refined diagrams, which one would you prefer for onboarding, and why?

## Response Sheet

Fill one row per rater per artifact.

| Rater | Artifact | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | Q11 | Q12 | Q13 | Q14 | Q15 |
|-------|----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|-----|-----|-----|
| R1 | Draft |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R1 | Refined |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R2 | Draft |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R2 | Refined |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R3 | Draft |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R3 | Refined |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R4 | Draft |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R4 | Refined |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## Suggested Aggregates

- Onboarding usefulness score: average of Q1-Q10
- Correctness and trust score: average of Q11-Q15
- Overall score: average of Q1-Q15

## Suggested Interpretation

- `4.5-5.0`: Excellent
- `3.5-4.4`: Good
- `2.5-3.4`: Mixed
- `1.5-2.4`: Weak
- `1.0-1.4`: Poor
