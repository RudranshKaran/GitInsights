# Database & API Planning

## Objective

This document defines the data storage strategy and API contracts for GitInsight. The goal is to support core functionality while keeping the system lightweight, scalable, and aligned with the MVP scope.

---

## Data Storage Strategy

GitInsight is primarily a **stateless analysis system**. Most evaluations are computed on demand and returned to the user without requiring persistent storage.

A database is used only where persistence adds real value.

---

## Database Choice

### Platform
Firebase (Firestore)

### Reasoning
- Serverless and low operational overhead
- Easy integration with backend services
- Suitable for lightweight persistence
- No complex relational requirements for MVP

---

## Data to be Stored (MVP)

### 1. Analysis Metadata
Stores minimal information about each analysis request.

**Collection: `analyses`**

| Field Name | Type | Description |
|-----------|------|-------------|
| analysis_id | string | Unique identifier |
| repo_url | string | GitHub repository URL |
| repo_name | string | Repository name |
| analysis_timestamp | timestamp | Time of analysis |
| overall_score | number | Final readiness score |
| status | string | completed / failed |
| version | string | Evaluation version |

---

### 2. Evaluation Report (Optional Persistence)

**Collection: `reports`**

| Field Name | Type | Description |
|-----------|------|-------------|
| analysis_id | string | Linked analysis ID |
| summary | string | High-level evaluation |
| strengths | array | Key strengths |
| improvements | array | Suggested improvements |
| resume_bullets | array | Resume-ready bullet points |
| section_scores | map | Section-wise scores |

> Note: Storing full reports is optional and can be disabled if not needed.

---

## Data That Is NOT Stored

- Source code files
- Repository contents
- API keys or secrets
- User credentials (no auth in MVP)

This ensures privacy and minimizes liability.

---

## API Design Principles

- RESTful endpoints
- Clear request and response formats
- Explicit error handling
- Stateless operations
- JSON-based communication

---

## API Endpoints

### 1. Analyze GitHub Repository

POST /analyze

#### Request Body
```json
{
  "repo_url": "https://github.com/username/repository"
}
```

#### Response Body
```json
{
  "analysis_id": "string",
  "repo_name": "string",
  "overall_score": number,
  "summary": "string",
  "strengths": ["string"],
  "improvements": ["string"],
  "resume_bullets": ["string"],
  "section_scores": {
    "documentation": number,
    "structure": number,
    "code_quality": number,
    "tech_stack": number
  }
}
```

---

### 2. Get Analysis Report (Optional)

GET /analysis/{analysis_id}

#### Response Body
```json
{
  "analysis_id": "string",
  "report": { ... }
}
```

---

### 3. Health Check

GET /health

#### Response Body
```json
{
  "status": "ok"
}
```

---

## Error Handling Strategy

| Scenario            | HTTP Code | Message                    |
| ------------------- | --------- | -------------------------- |
| Invalid GitHub URL  | 400       | Invalid repository URL     |
| Private repository  | 403       | Repository is not public   |
| GitHub API failure  | 502       | GitHub service unavailable |
| LLM failure         | 500       | Analysis failed            |
| Rate limit exceeded | 429       | Too many requests          |

Errors are returned in a consistent JSON format:
```json
{
  "error": "string",
  "details": "string"
}
```

---

## API Security Considerations
- Public endpoint access
- Rate limiting per IP
- Input validation and sanitization
- No authentication in MVP
- Environment-based API keys

---

## Versioning Strategy
- API versioning using URL prefix
```bash
/api/v1/analyze
```
- Enables future evolution without breaking clients

---

## Summary
The database and API design for GitInsight prioritizes simplicity, privacy, and scalability. By storing only essential metadata and designing clear API contracts, the system remains production-ready without unnecessary complexity.
