# GitInsight — Phase-Wise Execution Plan

## Core Philosophy (Read This First)

> **No phase moves forward unless the previous phase is stable, testable, and explainable.**

Rules:

* One responsibility per phase
* Deterministic before AI
* AI outputs always constrained
* Prompts treated as versioned code
* Every phase has a “definition of done”

---

## Phase 0: Project Scaffolding & Contracts (Foundation)

### Goal

Set up structure so later phases don’t become messy.

### What to build

* Repo structure
* API skeleton
* Data contracts (schemas)
* Prompt folder structure

### Deliverables

```
backend/
  app/
    api/
    services/
    pipelines/
    schemas/
    prompts/
    utils/
```

### Define (no implementation yet)

* `RepositoryData` schema
* `RuleEvaluationResult`
* `AIInsightResult`
* `FinalReport`

### Exit criteria

✅ FastAPI app runs
✅ `/health` endpoint works
✅ Schemas defined and reviewed

❗ No AI, no GitHub calls yet.

---

## Phase 1: Repository Ingestion (Zero AI)

### Goal

Reliably convert a GitHub URL into structured data.

### Responsibilities

* Validate GitHub URL
* Fetch repo metadata
* Fetch file tree
* Fetch README (if exists)

### Output (example)

```json
{
  "repo_name": "gitinsight",
  "files": [...],
  "readme": "...",
  "languages": {...}
}
```

### Tests

* Invalid URL
* Private repo
* Empty repo
* Large repo

### Exit criteria

✅ Same repo → same output
✅ No AI involved
✅ Errors are clean and descriptive

---

## Phase 2: Rule-Based Evaluation Engine (Deterministic Core)

### Goal

Create a **trustworthy baseline evaluation**.

### Responsibilities

* README presence & length
* Folder structure sanity
* Config file detection
* Project completeness signals

### Output

```json
{
  "documentation_score": 6,
  "structure_score": 7,
  "issues": ["Missing CONTRIBUTING.md"]
}
```

### Tests

* Deterministic scoring
* Same input → same output

### Exit criteria

✅ Fully deterministic
✅ Covers at least 60–70% of evaluation logic
✅ Zero AI dependency

This phase gives your project **credibility**.

---

## Phase 3: AI-Assisted Analysis (Constrained & Scoped)

### Goal

Use Gemini only where **human judgment is needed**.

### Responsibilities

* README quality analysis
* Code clarity signals
* Tech stack usage explanation
* Recruiter-style feedback

### Rules (non-negotiable)

* One prompt per concern
* JSON-only output
* Schema validation
* No scoring by AI

### Prompt structure

```
prompts/
  documentation_quality.prompt
  code_clarity.prompt
  tech_stack_analysis.prompt
```

### Tests

* Schema validation
* Retry on malformed output
* Timeout handling

### Exit criteria

✅ AI outputs always parseable
✅ AI does NOT assign scores
✅ Prompts are versioned

---

## Phase 4: Hybrid Scoring Engine (Trust Layer)

### Goal

Combine rules + AI into stable scores.

### Responsibilities

* Weighted scoring logic
* Score normalization
* Final internship-readiness score

### Example

```python
final_score = (
  0.4 * rule_scores +
  0.6 * ai_signals
)
```

### Tests

* Score stability
* Weight tuning
* Edge cases (missing sections)

### Exit criteria

✅ Same repo → similar score
✅ Scoring logic explainable
✅ Recruiter-aligned outputs

---

## Phase 5: Report & Resume Output Generation

### Goal

Turn raw data into **human-readable value**.

### Responsibilities

* Structured report generation
* Actionable improvement list
* Resume-ready bullet points

### Output

```json
{
  "summary": "...",
  "strengths": [...],
  "improvements": [...],
  "resume_bullets": [...]
}
```

### Tests

* Empty sections handled
* Bullets are concise & professional
* Copy-paste friendly

### Exit criteria

✅ Report readable in < 2 minutes
✅ Resume bullets sound recruiter-grade

---

## Phase 6: Frontend Integration & UX Polish

### Goal

Deliver the product experience.

### Responsibilities

* Repo input UI
* Loading states
* Report rendering
* Error handling UX

### Tests

* End-to-end flow
* Mobile responsiveness
* Error UX

### Exit criteria

✅ Smooth end-to-end flow
✅ No raw JSON exposed
✅ Polished UI

---

## Phase 7: Hardening & Final QA

### Goal

Make it demo-safe and interview-safe.

### Responsibilities

* Rate limiting
* Better errors
* Prompt tuning
* Performance limits

### Exit criteria

✅ No crashes
✅ Graceful failures
✅ Stable demo

---

## Visual Summary (Mental Model)

```
GitHub URL
   ↓
[Phase 1] Repo Ingestion
   ↓
[Phase 2] Rule Engine
   ↓
[Phase 3] AI Insights
   ↓
[Phase 4] Hybrid Scoring
   ↓
[Phase 5] Report Generator
   ↓
[Phase 6] UI
```

---
