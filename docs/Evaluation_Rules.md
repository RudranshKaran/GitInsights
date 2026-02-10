# Evaluation Rules

## Overview

This document defines the deterministic rules used by GitInsight to evaluate GitHub repositories. All evaluations are rule-based with zero AI dependency, ensuring consistent and explainable results.

**Core Principle**: Same input always produces the same output.

---

## Scoring Dimensions

GitInsight evaluates repositories across four dimensions, each scored on a **0–10 scale**:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Documentation | 25% | README quality and completeness |
| Structure | 25% | Project organization and file layout |
| Configuration | 25% | Essential config and metadata files |
| Completeness | 25% | Signals of a "finished" project |

---

## 1. Documentation Evaluation

Evaluates README quality using explicit, countable rules.

### Signals Detected

- README file exists
- README character count
- Presence of key sections:
  - Installation / Getting Started / Setup
  - Usage / How to Use / Examples
  - Features / Highlights
  - License

### Scoring Rules

| Condition | Points |
|-----------|--------|
| README missing | 0 (total) |
| README exists | +3 (base) |
| README ≥ 300 characters | +2 |
| README ≥ 800 characters | +2 |
| Each key section present | +1 (max +3) |

**Maximum Score**: 10

### Section Detection Patterns

Sections are detected using case-insensitive pattern matching:

| Section | Patterns Matched |
|---------|-----------------|
| Installation | `## Install`, `## Getting Started`, `## Setup`, `## Quick Start`, `## Prerequisites` |
| Usage | `## Usage`, `## How to Use`, `## Examples`, `## Running` |
| Features | `## Features`, `## Key Features`, `## Highlights`, `## What it Does` |
| License | `## License`, `## Licensing` |

### Issues Generated

- "README is missing"
- "README is too short (less than 300 characters)"
- "README is missing an Installation section"
- "README is missing a Usage section"
- "README is missing a Features section"
- "README is missing a License section"

---

## 2. Structure Evaluation

Evaluates repository organization and file layout.

### Signals Detected

- Presence of recognizable source directories
- Number of files at repository root
- Directory nesting depth

### Recognized Source Directories

```
src, source, lib, app, backend, frontend,
core, pkg, packages, modules, components
```

### Scoring Rules

| Condition | Points |
|-----------|--------|
| Base score | 5 |
| No recognizable source directory | −3 |
| Recognizable source directory present | +4 |
| Root files ≤ 10 | +3 |
| Root files > 10 | +0 |
| Deep nesting (>5 levels) without structure | −2 |

**Minimum Score**: 0  
**Maximum Score**: 12 (capped at 10 in practice)

### Issues Generated

- "No recognizable source directory found (e.g., src/, app/, backend/)"
- "Too many files in repository root (X files, recommended ≤ 10)"
- "Deep file nesting detected without clear directory structure"

---

## 3. Configuration Evaluation

Checks for essential configuration and metadata files.

### Files Detected

| Category | Files |
|----------|-------|
| Git Ignore | `.gitignore` |
| License | `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `COPYING.md` |
| Dependencies | `requirements.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `go.mod`, `Cargo.toml`, `Gemfile`, `build.gradle`, `pom.xml`, `composer.json`, `mix.exs`, `project.clj` |

### Scoring Rules

| Condition | Points |
|-----------|--------|
| `.gitignore` present | +3 |
| License file present | +3 |
| Dependency file present | +4 |

**Maximum Score**: 10

### Issues Generated

- "No .gitignore file found"
- "No LICENSE file found"
- "No dependency file found (e.g., requirements.txt, package.json)"

---

## 4. Completeness Evaluation

Evaluates signals that indicate a "finished" project.

### Signals Detected

| Signal | Description |
|--------|-------------|
| README | README file exists and is non-empty |
| License | License file present |
| Dependencies | Dependency management file present |
| Organization | Multiple directories present (≥2) |

### Scoring Rules

| Condition | Points |
|-----------|--------|
| Each signal present | +2.5 (rounded to integer) |

**Score Calculation**: `round(signals_present × 2.5)`

| Signals | Score |
|---------|-------|
| 0 | 0 |
| 1 | 3 |
| 2 | 5 |
| 3 | 8 |
| 4 | 10 |

### Issues Generated

- "Project appears incomplete: README is missing"
- "Project appears incomplete: LICENSE is missing"
- "Project appears incomplete: no dependency management file"
- "Project appears incomplete: lacks directory organization"

---

## Issue Reporting Guidelines

All issues follow these principles:

1. **Actionable** — Tell the user what to do
2. **Specific** — Mention exactly what's missing
3. **Non-judgmental** — No blame or criticism

### Examples

✅ Good: "README is missing an Installation section"  
❌ Bad: "Your README is poorly written"

✅ Good: "No LICENSE file found"  
❌ Bad: "You forgot to add a license"

---

## Determinism Guarantees

The evaluation engine guarantees:

- **Same input → Same output**: Identical repositories always produce identical scores
- **Order independence**: File order does not affect results
- **No randomness**: No probabilistic logic or AI inference
- **Explainability**: Every score deduction generates a traceable issue

---

## Example Output

```json
{
  "documentation_score": 7,
  "structure_score": 9,
  "configuration_score": 10,
  "completeness_score": 8,
  "issues": [
    "README is missing a Features section",
    "README is missing a License section"
  ]
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial rule set for Phase 2 |
