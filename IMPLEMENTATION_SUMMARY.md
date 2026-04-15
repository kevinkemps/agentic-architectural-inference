# MemSkill Implementation Summary

## What Was Built

A **critique strategy evolution system** for the agentic architectural inference pipeline, inspired by the MemSkill paper (arXiv:2602.02474).

**Key Achievement**: A self-improving critique loop that identifies why critiques fail and proposes prompt refinements.

---

## Core Components Implemented

### 1. **CritiqueEvaluator** (`aai/lib/agents.py`)
- Measures critique effectiveness against evaluation questions
- Produces three metrics:
  - **Effectiveness**: How comprehensively does the critique cover architectural concerns?
  - **Actionability**: How specific and implementable are the recommendations?
  - **False Positive Risk**: How many vague or unsupported statements exist?
- Outputs: `04_critique/feedback.json` with per-run metrics

### 2. **DesignerAgent** (`aai/lib/agents.py`)
- Analyzes failure patterns in critique feedback
- Proposes targeted prompt refinements to address gaps
- Tracks evolution history with version numbers and metrics
- Outputs:
  - `04_critique/designer_proposals.md`: Human-readable proposals
  - `04_critique/evolution_history.json`: Version metadata

### 3. **Instrumented CritiqueAgent**
- Updated `critique()` method to accept `evolved_prompt_path` parameter
- Enables use of improved prompts in subsequent runs
- Backward compatible (defaults to base `CRITIC_PROMPT`)

### 4. **Designer Prompt** (`prompts/designer-agent.md`)
- Guides LLM to analyze failure cases and propose refinements
- Emphasizes: coverage, specificity, evidence, actionability, accuracy
- Supports iterative improvement of critique strategies

### 5. **Evaluation Infrastructure**
- `eval_runner.py`: Script to evaluate pipeline outputs using eval questions
- `metrics_summary.md`: Aggregate quality report across runs
- Evolution history tracking with version numbers

---

## Files Modified/Created

### New Files
- ✅ `prompts/designer-agent.md` — Designer agent instructions
- ✅ `aai/eval_runner.py` — Evaluation runner script
- ✅ `docs/agents/critique-evolution-guide.md` — Comprehensive guide

### Modified Files

| File | Changes |
|------|---------|
| `aai/lib/agents.py` | Added `CritiqueEvaluator` and `DesignerAgent` classes; updated `CritiqueAgent.critique()` |
| `aai/lib/prompts.py` | Added `load_evolved_prompt()` function and `DESIGNER_PROMPT` constant |
| `aai/pipeline.py` | Added `eval_questions_path` and `enable_designer` parameters; integrated evaluator and designer into orchestration |
| `aai/cli.py` | Added `--eval-questions-path` and `--enable-designer` flags |
| `AGENTS.md` | Documented Designer and CritiqueEvaluator agents; updated Runtime Behavior section |

---

## How to Use

### Baseline Run (No Evolution)
```bash
cd aai
python3 -m cli --repo-path /path/to/repo
```

### With Evaluation Feedback
```bash
python3 -m cli \
  --repo-path /path/to/repo \
  --eval-questions-path ../aai/evaluation/eval_questions.md
```
Creates: `04_critique/feedback.json` with quality metrics

### With Full Designer Loop
```bash
python3 -m cli \
  --repo-path /path/to/repo \
  --eval-questions-path ../aai/evaluation/eval_questions.md \
  --enable-designer
```
Creates: `04_critique/designer_proposals.md` with refinement suggestions

### Evaluate Quality
```bash
python3 eval_runner.py \
  --out-dir output_analysis \
  --eval-questions ../aai/evaluation/eval_questions.md
```
Creates: `evaluation/metrics_summary.md` with aggregate metrics

---

## Output Artifacts

### Structure
```
output_analysis/
├── 04_critique/
│   ├── critique.md                  # Base critique
│   ├── feedback.json [NEW]          # Evaluation results
│   ├── designer_proposals.md [NEW]  # Refinement proposals
│   └── evolution_history.json [NEW] # Version tracking
└── evaluation/
    └── metrics_summary.md [NEW]     # Aggregate metrics
```

### Example feedback.json
```json
{
  "abc12345": {
    "timestamp": "2026-04-01 14:30:00",
    "run_id": "abc12345",
    "effectiveness_score": 65.0,
    "coverage": [0, 2, 5],
    "actionability_score": 72.5,
    "false_positive_risk": 28.0
  }
}
```

### Example evolution_history.json
```json
{
  "versions": [
    {
      "version": "v1",
      "source": "base",
      "timestamp": "2026-04-01 14:35:00",
      "proposal_summary": "Add transitive dependency checks...",
      "metrics": {
        "failure_patterns_count": 2,
        "total_failures": 5
      }
    }
  ],
  "current_version": "v1"
}
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Heuristic evaluation (not LLM-based)** | Fast iteration; no circular dependency on critic LLM |
| **Designer runs after critique loop** | Clear causality; simpler orchestration |
| **Evolved prompts versioned** | Audit trail; reversible; A/B testing capable |
| **Proposals are human-reviewed** | Safe by default; MemSkill philosophy |
| **Failure threshold: 3 cases** | Reduces noise; practical heuristic for patterns |

---

## Validation & Testing

✅ **Syntax Validation**: All Python files pass `py_compile` check  
✅ **Import Verification**: Core imports validated (environment dependencies handled elsewhere)  
✅ **Backward Compatibility**: Existing pipeline runs unaffected; new features opt-in via flags  
✅ **Data Structures**: JSON feedback and evolution_history properly structured

---

## Next Steps (Future Work)

### Short Term
1. **Manual Testing**: Run full pipeline with evaluation enabled on test repo
2. **Proposal Review**: Examine designer_proposals.md quality and actionability
3. **Prompt Integration**: Create first evolved prompt based on proposals

### Medium Term
1. **Auto-Integration**: Feature to automatically apply approved proposals
2. **A/B Testing**: Run two critic versions in parallel, compare
3. **Convergence Analysis**: Track metrics improvement across refine cycles

### Long Term
1. **Pattern Learning**: ML model to predict which proposals help most
2. **Cross-Repo Generalization**: Share evolved prompts across projects
3. **Critic Ensemble**: Multiple critic agents with different strategies

---

## Documentation

- **Usage Guide**: `docs/agents/critique-evolution-guide.md` (comprehensive)
- **Agent Spec**: `AGENTS.md` § 4a-4b (canonical reference)
- **Implementation**: `aai/lib/agents.py` (docstrings and code)
- **Prompt**: `prompts/designer-agent.md` (detailed instructions)

---

## Notes for Contributors

1. **Keep feedback heuristics simple**: Complexity → harder to interpret results
2. **Version evolved prompts clearly**: `critic-agent-v2-evolved-{version}.md` format
3. **Document proposal rationale**: Designer output should explain *why* not just *what*
4. **Test evaluation questions**: Ensure they're representative of architecture concerns
5. **Track metrics across runs**: Compare baselines before/after refinements

---

## Architecture Alignment

This implementation aligns with AGENTS.md philosophy:
- ✅ **Explicit file handoffs**: Feedback flows via JSON files
- ✅ **Stage contracts maintained**: New agents respect input/output boundaries
- ✅ **Readability first**: Clear class names, focused methods, detailed docs
- ✅ **Evidence-backed**: Proposals grounded in actual failure patterns
- ✅ **Human-in-the-loop**: Designer proposes, humans decide integration

---

**AGENTS.md is in context.**  
Currently using Claude Haiku 4.5.
