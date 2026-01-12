# Product Requirements Document (PRD – Lite)

## Product Name
GitInsight – AI GitHub Project Reviewer

---

## Objective

The objective of GitInsight is to help students and early-stage developers evaluate and improve their GitHub projects by providing structured, actionable feedback aligned with internship and recruiter expectations.

The product focuses on **clarity, readiness, and presentation**, not on replacing full code reviews or static analysis tools.

---

## Target Users

- Students applying for internships or entry-level roles
- Early-stage developers building portfolio projects
- Hackathon participants seeking project feedback

---

## Core Problem

Users lack a reliable way to assess whether their GitHub projects are internship-ready and do not receive clear guidance on what to improve or how to present their work professionally.

---

## In-Scope Features (MVP)

### 1. GitHub Repository Input
- Accepts a public GitHub repository URL
- Fetches repository metadata and contents using GitHub APIs

---

### 2. Project Structure & Documentation Analysis
- Evaluates folder organization and file structure
- Analyzes README quality and completeness
- Checks presence of essential documentation files

---

### 3. Code Quality & Tech Stack Evaluation
- Reviews code clarity at a high level
- Identifies main technologies and frameworks used
- Assesses consistency and maintainability signals

---

### 4. Internship-Readiness Scoring
- Scores the project across predefined rubrics such as:
  - Documentation quality
  - Project clarity
  - Code organization
  - Technical depth
- Outputs an overall readiness score

---

### 5. Actionable Improvement Suggestions
- Provides specific, prioritized recommendations
- Suggests documentation improvements and structural fixes
- Highlights missing or weak areas

---

### 6. Resume-Ready Output Generation
- Generates concise, professional resume bullet points
- Emphasizes impact, technologies, and problem-solving

---

### 7. Structured Evaluation Report
- Produces a readable, sectioned report
- Suitable for student review and iteration

---

## Out-of-Scope Features (Not in MVP)

The following features are intentionally excluded to maintain focus:

- Private repository analysis
- Live code execution or debugging
- Full static code analysis or linting replacement
- Recruiter dashboards or analytics
- Automatic code refactoring or pull requests
- Resume parsing or job matching

---

## Nice-to-Have Features (Post-MVP)

- Project comparison across multiple repositories
- Progress tracking across project versions
- Custom scoring rubrics for different roles
- Exportable reports (PDF)
- Recruiter or mentor review mode

---

## Assumptions

- Users will provide public GitHub repositories
- README and repository contents are accessible
- Initial users are students and early developers
- AI-generated feedback is advisory, not authoritative

---

## Constraints

- Limited development time and resources
- Dependence on GitHub API rate limits
- Accuracy limited by repository content quality
- No access to private or proprietary code

---

## Success Criteria

- Users receive clear, understandable evaluations
- Feedback is actionable and easy to implement
- Resume bullets are relevant and concise
- The system remains fast and simple to use

---

## Non-Goals

- Replacing human code reviews
- Acting as a full recruitment platform
- Teaching programming from scratch

---

## Summary

GitInsight focuses on delivering meaningful, recruiter-aligned feedback for GitHub projects while maintaining a tight, achievable scope. By prioritizing clarity and actionability, the product ensures real value without unnecessary complexity.
