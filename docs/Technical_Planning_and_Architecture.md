# Technical Planning & Architecture

## Objective

This document defines the technical architecture, technology stack, and system design decisions for GitInsight. The goal is to build a **production-realistic, scalable, and fully open-source system** that evaluates GitHub projects using a hybrid AI-driven approach aligned with recruiter expectations.

---

## System Overview

GitInsight is a web-based application that accepts a public GitHub repository URL, analyzes the repository using a multi-step evaluation pipeline, and generates a structured, recruiter-style evaluation report.

The system is designed with:
- A Python-based backend
- AI-powered analysis using Gemini
- A polished frontend interface
- Live deployment for real-world usage

---

## High-Level Architecture

Frontend (Web UI)
|
v
Backend API (FastAPI)
|
├── GitHub Data Fetching Layer
├── Evaluation Pipeline (Hybrid Logic)
├── LLM Orchestration (Gemini via LangChain)
|
v
Report Generation & Scoring Engine

---

## Technology Stack

### Backend
- **Language**: Python
- **Framework**: FastAPI
- **Reasoning**:
  - Async support for long-running tasks
  - Clean API design
  - Production-grade performance
  - Strong ecosystem support

---

### AI & LLM Layer
- **LLM Provider**: Google Gemini
- **Orchestration**: LangChain
- **Reasoning**:
  - Gemini for strong reasoning and summarization
  - LangChain for multi-step pipelines
  - Supports hybrid (rules + AI) evaluations
  - Clean separation of prompts and logic

---

### Frontend
- **Framework**: React / Next.js (deployed on Vercel)
- **Reasoning**:
  - Polished, modern UI
  - SEO-friendly
  - Fast iteration
  - Industry-standard frontend stack

---

### Data & Persistence (Optional / Lightweight)
- **Platform**: Firebase
- **Usage (If needed)**:
  - Storing analysis history
  - Rate limiting
  - Basic user analytics
- **Reasoning**:
  - Serverless
  - Easy integration
  - No heavy database overhead for MVP

---

### Deployment
- **Frontend**: Vercel
- **Backend**: Cloud VM / container-based hosting (Render, Railway, or similar)
- **Secrets Management**:
  - Environment variables
  - No secrets committed to repo

---

## GitHub Data Access Strategy

### Approach
- **GitHub REST API** (primary)
- **Selective repository cloning** (if needed for large repos)

### Reasoning
- REST API is simpler and more stable for MVP
- Full repository analysis supported
- Safer handling of rate limits
- Avoids unnecessary GraphQL complexity

---

## Evaluation Pipeline (Multi-Step)

The analysis follows a **sequential pipeline**, not a single prompt.

### Step 1: Repository Ingestion
- Fetch file tree
- Identify key files (README, config, source folders)
- Extract metadata

---

### Step 2: Rule-Based Analysis
- Documentation presence
- Project structure sanity
- File organization
- Missing critical files

*(Deterministic & repeatable)*

---

### Step 3: AI-Assisted Evaluation
Using Gemini via LangChain:
- Documentation quality analysis
- Code clarity signals
- Tech stack usage assessment
- Recruiter-style qualitative feedback

---

### Step 4: Hybrid Scoring Engine
- Predefined rubrics with weighted scores
- AI provides judgments
- Rules enforce consistency
- Produces deterministic-enough results for credibility

---

### Step 5: Report Generation
- Structured sections
- Clear headings
- Actionable recommendations
- Resume-ready bullet points

---

## Scoring Philosophy

- Scores are **guidance-oriented**, not absolute judgments
- Same input should produce **similar outputs**
- AI variability constrained using rubrics and prompts
- Recruiter tone prioritized over academic tone

---

## API Design (High-Level)

### Core Endpoint

POST /analyze

**Input**
- GitHub repository URL

**Output**
- Project overview
- Section-wise scores
- Strengths & weaknesses
- Improvement suggestions
- Resume-ready bullets

---

## Security Considerations

- Public repositories only
- No user authentication in MVP
- API rate limiting
- Input validation
- Environment-based secret handling

---

## Scalability Assumptions

- Target users: Hundreds
- Concurrent analysis: Limited
- Async processing to prevent blocking
- Horizontal scaling possible if needed

---

## Open-Source Strategy

- Fully open-source repository
- Clear README and setup instructions
- Modular architecture
- No vendor lock-in

---

## Constraints & Trade-Offs

- No private repo support
- No real-time collaboration
- No automated code refactoring
- AI feedback is advisory, not authoritative

---

## Summary

GitInsight uses a production-realistic, Python-first architecture that combines deterministic rules with AI reasoning to evaluate GitHub projects from a recruiter’s perspective. The system balances credibility, scalability, and implementation feasibility while remaining fully open-source and internship-ready.
