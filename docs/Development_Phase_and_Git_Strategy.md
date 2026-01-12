# Development Phase & Git Strategy

## Objective

This document defines the development workflow and Git practices used in the GitInsight project. The goal is to ensure clean collaboration, traceable changes, and maintainable code aligned with industry standards.

---

## Development Principles

- Write clean, readable, and modular code
- Follow separation of concerns
- Prefer clarity over cleverness
- Keep the main branch stable
- Small, meaningful commits

---

## Repository Structure
```
gitinsight/
│
├── backend/
│ ├── app/
│ │ ├── api/
│ │ ├── services/
│ │ ├── pipelines/
│ │ ├── models/
│ │ ├── utils/
│ │ └── main.py
│ │
│ ├── tests/
│ └── requirements.txt
│
├── frontend/
│ └── (Next.js application)
│
├── docs/
│ ├── Problem_Statement.md
│ ├── Market_and_User_Research.md
│ ├── PRD_Lite.md
│ ├── User_Experience_Planning.md
│ ├── Wireframing_and_UX_Design.md
│ ├── UI_Design_and_Design_System.md
│ ├── Technical_Planning_and_Architecture.md
│ ├── Database_and_API_Planning.md
│ └── Development_Phase_and_Git_Strategy.md
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## Branching Strategy

### Branches

- `main`
  - Always stable
  - Production-ready code only

- `dev`
  - Integration branch
  - Features merged here first

- `feature/*`
  - Individual feature development
  - Examples:
    - `feature/repo-ingestion`
    - `feature/evaluation-pipeline`
    - `feature/report-generation`

---

## Branch Workflow

1. Create feature branch from `dev`
2. Develop feature with focused commits
3. Test locally
4. Merge feature branch into `dev`
5. Periodically merge `dev` into `main`

---

## Commit Message Convention

Follow a simple, consistent format:
```
<type>: <short description>
```

### Allowed Types
- `feat` – New feature
- `fix` – Bug fix
- `docs` – Documentation changes
- `refactor` – Code restructuring
- `test` – Tests added or updated
- `chore` – Tooling or config changes

### Examples
- `feat: add repository ingestion pipeline`
- `docs: add PRD and UX planning documents`
- `fix: handle invalid GitHub URLs`
- `refactor: simplify evaluation scoring logic`

---

## Pull Request Guidelines

- One feature per pull request
- Clear title and description
- Reference related issues or features
- Ensure code passes basic tests
- Avoid large, unreviewable PRs

---

## Code Quality Practices

- Type hints where applicable
- Clear function and variable naming
- Docstrings for complex logic
- Avoid deeply nested logic
- Reusable utility functions

---

## Testing During Development

- Unit tests for core logic
- Mock external APIs (GitHub, Gemini)
- Test error cases explicitly

---

## Environment Management

- Use `.env` files for local development
- Never commit secrets
- Separate dev and production configurations

---

## Development Milestones

1. Backend scaffolding and API setup
2. GitHub data ingestion
3. Evaluation pipeline implementation
4. Scoring and report generation
5. Frontend integration
6. End-to-end testing
7. Deployment

---

## Summary

The development workflow and Git strategy for GitInsight emphasize clarity, discipline, and maintainability. By following structured branching and clean commit practices, the project remains scalable, collaborative, and professional.

