# Critique Strategy Evolution: Implementation Guide

## Overview

This document explains the MemSkill-inspired critic strategy evolution system added to the agentic architectural inference pipeline.

**Key Components**:
- **CritiqueEvaluator**: Measures critique effectiveness against evaluation questions
- **DesignerAgent**: Proposes prompt refinements based on failure patterns
- **Evolution Persistence**: Versioned prompts tracked with metrics in `evolution_history.json`

## Usage

### Basic Usage (Without Evolution)

Run the pipeline normally:
```bash
cd aai
python3 -m cli --repo-path /path/to/repo
```

### With Critique Evaluation

Enable feedback collection to track critique quality:
```bash
python3 -m cli \
  --repo-path /path/to/repo \
  --eval-questions-path ../aai/evaluation/eval_questions.md
```

This creates:
- `output_analysis/04_critique/feedback.json`: Detailed evaluation results per run
- `output_analysis/evaluation/metrics_summary.md`: Aggregate metrics report

### With Designer Evolution (Full Closed-Loop)

Enable both evaluation and designer to propose prompt refinements:
```bash
python3 -m cli \
  --repo-path /path/to/repo \
  --eval-questions-path ../aai/evaluation/eval_questions.md \
  --enable-designer
```

This additionally creates:
- `output_analysis/04_critique/designer_proposals.md`: Proposed refinements
- `output_analysis/04_critique/evolution_history.json`: Version history with metrics

## How It Works

### Stage 1: Evaluation (CritiqueEvaluator)

After each critique is generated, the Evaluator:
1. Loads the critique output
2. Compares it against evaluation questions using heuristic scoring
3. Generates metrics:
   - **Effectiveness**: % of eval questions addressed (0-100)
   - **Actionability**: # concrete recommendations found (0-100)
   - **False Positive Risk**: # vague language patterns (0-50)
4. Saves results to `feedback.json`

**Example feedback.json**:
```json
{
  "abc123": {
    "timestamp": "2026-04-01 14:30:00",
    "effectiveness_score": 65.0,
    "coverage": [0, 3, 5],
    "actionability_score": 75.0,
    "false_positive_risk": 25.0
  }
}
```

### Stage 2: Analysis (DesignerAgent)

When failures accumulate (3+ cases by default), the Designer:
1. Groups failures by pattern (low effectiveness, high false positives, low actionability)
2. Loads source context (summaries, draft diagram, critique)
3. Calls the LLM with:
   - The identified failure patterns
   - Original summaries (source of truth)
   - The failed critique
   - Instructions to propose refinements
4. Returns human-readable proposals with rationale

**Example designer_proposals.md excerpt**:
```markdown
## Failure Pattern: Low Effectiveness

### Root Cause Analysis
The critique missed module dependencies because it focused only on direct imports,
ignoring indirect transitive dependencies through middleware layers.

### Prompt Refinement
Add: "Check for transitive dependencies through middleware/adapter layers. 
Do not limit analysis to direct import statements only."

### Rationale
Indirect dependencies are architectural concerns that current critique overlooks.
Adding this check will improve coverage of dependency patterns.

### Example
Before: "Module A depends on C" 
After: "Module A depends on C directly, and on D transitively through middleware B"
```

### Stage 3: Version Management

Evolution history tracked in `evolution_history.json`:
```json
{
  "versions": [
    {
      "version": "v1",
      "source": "base",
      "timestamp": "2026-04-01 14:35:00",
      "proposal_summary": "Add transitive dependency checks",
      "metrics": {
        "failure_patterns_count": 2,
        "total_failures": 5,
        "patterns": [...]
      }
    }
  ],
  "current_version": "v1"
}
```

Evolved prompts stored as: `prompts/critic-agent-v2-evolved-v1.md`

## Architecture

### File Structure (Output Artifacts)

```
output_analysis/
├── 04_critique/
│   ├── critique.md                    # Base critique output
│   ├── feedback.json                  # Evaluation results (new)
│   ├── designer_proposals.md          # Refinement proposals (new)
│   └── evolution_history.json         # Version tracking (new)
└── evaluation/
    └── metrics_summary.md             # Aggregate metrics (new)
```

### Code Structure (Implementation)

**New Classes in `aai/lib/agents.py`:**

1. **CritiqueEvaluator**
   - `load_eval_questions()`: Load markdown eval questions
   - `evaluate_critique()`: Score a critique, return metrics
   - `save_feedback()`: Write JSON feedback with timestamp+UUID
   - `evaluate()`: Main entry point

2. **DesignerAgent**
   - `load_feedback()`: Read feedback.json
   - `identify_failure_patterns()`: Group failures by type
   - `propose_refinement()`: Call LLM to generate proposals
   - `save_proposals()`: Write designer_proposals.md
   - `update_evolution_history()`: Track version in JSON
   - `design()`: Main entry point

**Updated Classes:**

- **CritiqueAgent**: Added `evolved_prompt_path` parameter to `critique()` method
  - Supports loading improved prompts for future runs
  - Backward compatible (defaults to base CRITIC_PROMPT)

**New in `aai/lib/prompts.py`:**
- `load_evolved_prompt(version)`: Load versioned critique prompts
- `DESIGNER_PROMPT`: Prompt for designer agent

**Updated `aai/pipeline.py`:**
- `run_pipeline()` accepts `eval_questions_path` and `enable_designer` flags
- After critique loop, runs CritiqueEvaluator if eval_questions provided
- After evaluation, optionally runs DesignerAgent if enabled

**Updated `aai/cli.py`:**
- `--eval-questions-path`: Path to markdown file with eval questions
- `--enable-designer`: Enable prompt evolution feature

## Workflow: End-to-End Example

### Run 1: Baseline

```bash
python3 -m cli --repo-path ./myrepo --eval-questions-path eval_questions.md
```

**Output**: 
- `03_draft/mermaid.md` (draft diagram)
- `04_critique/critique.md` (base critique)
- `04_critique/feedback.json` with baseline scores

### Run 2: Designer Analyzes & Proposes

```bash
python3 -m cli --repo-path ./myrepo \
  --eval-questions-path eval_questions.md \
  --enable-designer
```

**Output**: 
- Same as Run 1, plus:
- `04_critique/designer_proposals.md` (Designer's suggestions)
- `04_critique/evolution_history.json` (v1 proposal tracked)

### Manual Review & Integration

1. Examine `designer_proposals.md`
2. If proposals look good:
   - Copy approved proposals into a new prompt file
   - Save as `prompts/critic-agent-v2-evolved-v1.md`
3. If proposals need tweaking:
   - Edit them, then save as evolved file

### Run 3: Using Evolved Prompt (Future Work)

Future enhancement (not yet implemented):
```bash
python3 -m cli --repo-path ./myrepo --use-evolved-prompt v1
```

This would invoke `CritiqueAgent.critique(..., evolved_prompt_path='prompts/critic-agent-v2-evolved-v1.md')`

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Designer runs *after* critique loop, not during | Clear causality; simple orchestration; allows full cycle feedback |
| Evolved prompts *versioned*, not replaced | Audit trail; revertible; A/B testing capability |
| Feedback driven by eval_questions only | Focused signal; limited ground truth; avoids data drift |
| Proposals are human-reviewed | MemSkill philosophy; safe by default; user retains control |
| Default failure threshold: 3 cases | Reduces noise; prevents premature refinement; practical heuristic |
| Heuristic evaluation (not LLM-based scoring) | Faster iteration; no circular dependency on critic LLM |

## Evaluation Metrics Explained

### Effectiveness Score (0-100)
- Measures: Does the critique address content in the evaluation questions?
- How: Counts keyword matches between critique and eval questions
- Interpretation: 
  - 80+: Comprehensive coverage of most eval dimensions
  - 50-79: Partial coverage, some gaps
  - <50: Missing major architectural concerns

### Actionability Score (0-100)
- Measures: Are recommendations concrete and executable?
- How: Counts action verbs ("add", "remove", "refactor", etc.)
- Interpretation:
  - 80+: Specific, implementable feedback
  - 50-79: Mix of specific and vague guidance
  - <50: Mostly abstract or unclear recommendations

### False Positive Risk (0-50)
- Measures: How many vague or unsupported statements?
- How: Counts hedge phrases ("might", "could", "seems", etc.)
- Interpretation:
  - <15: Low risk; feedback is well-grounded
  - 15-30: Moderate risk; some unvalidated claims
  - >30: High risk; many speculative statements

## Troubleshooting

### "No feedback data available. Skipping Designer."
**Cause**: Evaluation not enabled or no prior critiques run  
**Fix**: Run pipeline with `--eval-questions-path` first

### "Insufficient failures. Skipping Designer."
**Cause**: Too few failed critiques to identify patterns  
**Fix**: Run multiple times or lower `failure_threshold` in DesignerAgent.__init__

### "Could not load evolved prompt"
**Cause**: Evolved prompt file not found  
**Fix**: Verify filename matches pattern `prompts/critic-agent-v2-evolved-*.md`

## Future Enhancements

1. **Auto-Integration**: Automatically apply approved proposals to next prompt version
2. **A/B Testing**: Run two critic versions in parallel, compare metrics
3. **Confidence Scoring**: LLM confidence in proposals; filter by quality threshold
4. **Pattern Learning**: Machine learning model to predict which proposals help most
5. **Cross-Repo Generalization**: Identify which refinements help across repos
6. **Divergence Detection**: Alert when evolved prompts drift too far from base

## References

- See [AGENTS.md](../AGENTS.md) for stage contracts
- See [critic-agent-v2.md](../prompts/critic-agent-v2.md) for base critique prompt
- See [designer-agent.md](../prompts/designer-agent.md) for designer instructions
- MemSkill paper: "Learning and Evolving Memory Skills for Self-Evolving Agents" (arXiv:2602.02474)
