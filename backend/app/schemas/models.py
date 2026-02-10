"""
Pydantic Data Models

This module defines all data contracts used throughout the application.
These schemas ensure type safety and validation for API requests, responses,
and internal data structures.
"""

from pydantic import BaseModel, Field
from typing import Any


# ============================================================================
# Ingestion Models (Phase 1)
# ============================================================================

class IngestRequest(BaseModel):
    """Request model for repository ingestion."""
    github_url: str = Field(..., description="Public GitHub repository URL")


class FileEntryResponse(BaseModel):
    """Represents a file or directory in the repository."""
    path: str = Field(..., description="Full path of the file/directory")
    name: str = Field(..., description="File or directory name")
    extension: str | None = Field(None, description="File extension (null for directories)")
    type: str = Field(..., description="Entry type: 'file' or 'directory'")


class IngestSuccessResponse(BaseModel):
    """
    Successful ingestion response matching Phase 1 output schema.
    
    This is deterministic structured data with no AI interpretation.
    """
    repo_name: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner username")
    default_branch: str = Field(..., description="Default branch name")
    languages: dict[str, int] = Field(default_factory=dict, description="Language breakdown in bytes")
    files: list[FileEntryResponse] = Field(default_factory=list, description="Repository file tree")
    readme: str | None = Field(None, description="README content if present")


class IngestErrorDetail(BaseModel):
    """Detailed error information."""
    type: str = Field(..., description="Error type: INVALID_URL | PRIVATE_REPO | NOT_FOUND | RATE_LIMITED | UNKNOWN")
    message: str = Field(..., description="Human-readable error message")
    details: str | None = Field(None, description="Optional technical details")


class IngestErrorResponse(BaseModel):
    """Error response for ingestion failures."""
    error: IngestErrorDetail


# ============================================================================
# Repository Data Models
# ============================================================================

class RepositoryData(BaseModel):
    """
    Represents parsed repository information fetched from GitHub.
    
    This model contains the essential metadata and content extracted
    from a GitHub repository for analysis.
    """
    
    repo_name: str = Field(..., description="Name of the repository (e.g., 'username/repo')")
    repo_url: str = Field(..., description="Full URL of the GitHub repository")
    default_branch: str = Field(..., description="Default branch name (e.g., 'main' or 'master')")
    files: list[str] = Field(default_factory=list, description="List of file paths in the repository")
    languages: dict[str, int] = Field(default_factory=dict, description="Programming languages and their byte counts")
    readme_content: str | None = Field(None, description="Content of the README file if present")


class RuleEvaluationResult(BaseModel):
    """
    Represents the output of deterministic rule-based evaluation.
    
    This model contains scores and issues identified through
    predefined rules and heuristics (non-AI based analysis).
    
    All scores are on a 0-10 scale for human readability.
    Same input must always produce the same output (deterministic).
    """
    
    documentation_score: int = Field(..., ge=0, le=10, description="Score for documentation quality (0-10)")
    structure_score: int = Field(..., ge=0, le=10, description="Score for project structure (0-10)")
    configuration_score: int = Field(..., ge=0, le=10, description="Score for configuration and metadata files (0-10)")
    completeness_score: int = Field(..., ge=0, le=10, description="Score for project completeness signals (0-10)")
    issues: list[str] = Field(default_factory=list, description="List of identified issues - actionable, specific, non-judgmental")


class AIInsightResult(BaseModel):
    """
    Represents AI-generated qualitative insights and recommendations.
    
    This model contains the output from LLM analysis, providing
    human-readable feedback on project quality.
    """
    
    summary: str = Field(..., description="High-level summary of the project evaluation")
    strengths: list[str] = Field(default_factory=list, description="Key strengths identified in the project")
    improvements: list[str] = Field(default_factory=list, description="Suggested improvements and action items")


# ============================================================================
# Phase 3: AI Analysis Response Schemas (Schema-Validated)
# ============================================================================

from typing import Literal


class DocumentationQualityResult(BaseModel):
    """
    AI-generated documentation quality analysis.
    
    Provides qualitative assessment of README clarity and usefulness.
    Does NOT include scores - only categorical assessments.
    """
    
    clarity: Literal["low", "medium", "high"] = Field(
        ..., description="Overall clarity level of documentation"
    )
    strengths: list[str] = Field(
        default_factory=list, 
        max_length=5,
        description="Positive aspects of documentation (max 5)"
    )
    gaps: list[str] = Field(
        default_factory=list,
        max_length=5, 
        description="Missing or unclear areas (max 5)"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Actionable improvement suggestions (max 5)"
    )


class CodeClarityResult(BaseModel):
    """
    AI-generated code clarity signals from structure analysis.
    
    Infers clarity from file/folder structure only - not code content.
    Does NOT include scores - only categorical assessments.
    """
    
    organization: Literal["poor", "acceptable", "well-structured"] = Field(
        ..., description="How well the project is organized structurally"
    )
    naming_consistency: Literal["low", "medium", "high"] = Field(
        ..., description="Consistency of naming conventions"
    )
    maintainability_signals: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Positive indicators for maintenance (max 5)"
    )
    concerns: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Structural issues affecting clarity (max 5)"
    )


class TechStackResult(BaseModel):
    """
    AI-generated tech stack usage explanation.
    
    Explains detected technologies as a recruiter would understand.
    Based only on detected languages and files - no assumptions.
    """
    
    primary_stack: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Main languages/frameworks detected (max 5)"
    )
    supporting_tools: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Secondary tools and utilities (max 5)"
    )
    usage_explanation: str = Field(
        ..., description="1-2 sentence explanation of stack usage"
    )
    missing_expectations: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Expected but missing complementary tools (max 3)"
    )


class RecruiterFeedbackResult(BaseModel):
    """
    AI-generated recruiter-style feedback.
    
    Constructive, professional feedback from hiring perspective.
    Neutral, encouraging, actionable, non-judgmental tone.
    """
    
    overall_impression: str = Field(
        ..., description="1-2 sentence neutral summary from recruiter perspective"
    )
    what_stands_out: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Positive aspects a recruiter would notice (max 5)"
    )
    what_needs_work: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Areas needing improvement for internship readiness (max 5)"
    )


class AIAnalysisError(BaseModel):
    """
    Structured error response for AI analysis failures.
    
    Returned when schema validation fails, timeout occurs, or unknown error.
    """
    
    type: Literal["SCHEMA_VALIDATION_FAILED", "TIMEOUT", "UNKNOWN"] = Field(
        ..., description="Error type classification"
    )
    message: str = Field(..., description="Human-readable error message")


class AIAnalysisErrorResponse(BaseModel):
    """Wrapper for AI analysis error."""
    error: AIAnalysisError


class CombinedAIInsights(BaseModel):
    """
    Combined results from all four AI analysis prompts.
    
    Aggregates documentation, code clarity, tech stack, and recruiter feedback.
    Used internally before generating final AIInsightResult.
    """
    
    documentation: DocumentationQualityResult | None = Field(
        None, description="Documentation quality analysis"
    )
    code_clarity: CodeClarityResult | None = Field(
        None, description="Code clarity signals"
    )
    tech_stack: TechStackResult | None = Field(
        None, description="Tech stack explanation"
    )
    recruiter_feedback: RecruiterFeedbackResult | None = Field(
        None, description="Recruiter-style feedback"
    )
    errors: list[AIAnalysisError] = Field(
        default_factory=list, description="Any errors encountered during analysis"
    )


class FinalReport(BaseModel):
    """
    Represents the complete evaluation report combining rule-based and AI analysis.
    
    This is the final output returned to users, containing all evaluation
    results, scores, insights, and recommendations.
    
    Phase 5 additions:
    - executive_summary: Human-readable 3-5 sentence summary
    - strengths: Key strengths derived from analysis (max 5)
    - improvements: Actionable improvement areas (max 5)
    """
    
    repo_name: str = Field(..., description="Name of the analyzed repository")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall project quality score (0-100)")
    rule_evaluation: RuleEvaluationResult = Field(..., description="Results from rule-based analysis")
    ai_insights: AIInsightResult = Field(..., description="Results from AI-powered analysis")
    resume_bullets: list[str] = Field(default_factory=list, max_length=4, description="Resume-ready bullet points (max 4)")
    
    # Phase 5: Report Generation outputs
    executive_summary: str = Field(
        default="",
        description="Human-readable executive summary (3-5 sentences, recruiter-style tone)"
    )
    strengths: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Key strengths derived from analysis (max 5)"
    )
    improvements: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Actionable improvement areas (max 5)"
    )


# ============================================================================
# Phase 4: Hybrid Scoring Engine Schemas
# ============================================================================

class HybridScoreBreakdown(BaseModel):
    """
    Weight breakdown for hybrid score computation.
    
    Documents the weights applied to rule-based vs AI-derived scores.
    Ensures transparency and explainability.
    """
    
    rules_weight: float = Field(default=0.4, description="Weight applied to rule-based composite score")
    ai_weight: float = Field(default=0.6, description="Weight applied to AI signal score")


class HybridScoringResult(BaseModel):
    """
    Output of the Hybrid Scoring Engine (Phase 4).
    
    Combines deterministic rule-based scores with quantified AI signals
    into a stable, explainable final score.
    
    All scores are on a 0-10 scale.
    Same input must always produce the same output (deterministic).
    """
    
    rule_composite_score: float = Field(
        ..., ge=0.0, le=10.0, description="Average of four rule-based scores (0-10)"
    )
    ai_signal_score: float = Field(
        ..., ge=0.0, le=10.0, description="Quantified AI signals score (0-10)"
    )
    final_score: float = Field(
        ..., ge=0.0, le=10.0, description="Weighted hybrid score (0-10), rounded to 1 decimal"
    )
    score_breakdown: HybridScoreBreakdown = Field(
        default_factory=lambda: HybridScoreBreakdown(),
        description="Weight breakdown for transparency"
    )


class HybridScoringErrorDetail(BaseModel):
    """
    Structured error for hybrid scoring failures.
    
    Returned when computation cannot be completed due to missing or invalid input.
    """
    
    type: Literal["MISSING_INPUT", "INVALID_RANGE", "UNKNOWN"] = Field(
        ..., description="Error type classification"
    )
    message: str = Field(..., description="Human-readable error message")


class HybridScoringError(BaseModel):
    """Wrapper for hybrid scoring error response."""
    error: HybridScoringErrorDetail


# ============================================================================
# Phase 5: Report Generation Schemas
# ============================================================================

class RepoMetadata(BaseModel):
    """Repository metadata for report generation."""
    repo_name: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner")


class RuleEngineOutput(BaseModel):
    """Structured output from Phase 2 rule-based evaluation."""
    documentation_score: int = Field(..., ge=0, le=10, description="Documentation score (0-10)")
    structure_score: int = Field(..., ge=0, le=10, description="Structure score (0-10)")
    configuration_score: int = Field(..., ge=0, le=10, description="Configuration score (0-10)")
    completeness_score: int = Field(..., ge=0, le=10, description="Completeness score (0-10)")
    issues: list[str] = Field(default_factory=list, description="List of identified issues")


class AIInsightsPayload(BaseModel):
    """
    Combined AI insights from Phase 3.
    
    This consolidates all AI analysis results for report generation.
    """
    documentation_quality: DocumentationQualityResult | None = None
    code_clarity: CodeClarityResult | None = None
    tech_stack_analysis: TechStackResult | None = None
    recruiter_feedback: RecruiterFeedbackResult | None = None


class FinalScores(BaseModel):
    """Final scores from Phase 4 hybrid scoring."""
    rule_composite_score: float = Field(..., ge=0.0, le=10.0, description="Rule-based composite score")
    ai_signal_score: float = Field(..., ge=0.0, le=10.0, description="AI signal score")
    final_score: float = Field(..., ge=0.0, le=10.0, description="Final hybrid score")


class ReportGenerationInput(BaseModel):
    """
    Consolidated input payload for Phase 5 report generation.
    
    Contains all data from Phases 1-4 needed to generate
    human-readable outputs.
    """
    repo_metadata: RepoMetadata = Field(..., description="Repository metadata")
    rule_engine_output: RuleEngineOutput = Field(..., description="Rule-based evaluation results")
    ai_insights: AIInsightsPayload = Field(..., description="AI analysis insights")
    final_scores: FinalScores = Field(..., description="Hybrid scoring results")


class ReportGenerationOutput(BaseModel):
    """
    Output from Phase 5 report generation.
    
    Contains human-readable, recruiter-friendly outputs derived
    strictly from the input data.
    """
    summary: str = Field(
        ..., 
        description="Executive summary (3-5 sentences, recruiter-style tone)"
    )
    strengths: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Key strengths derived from analysis (max 5)"
    )
    improvements: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Actionable improvement areas (max 5)"
    )
    resume_bullets: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Resume-ready bullet points (max 4)"
    )


class ReportGenerationErrorDetail(BaseModel):
    """Structured error for report generation failures."""
    type: Literal["MISSING_INPUT", "INVALID_STRUCTURE", "UNKNOWN"] = Field(
        ..., description="Error type classification"
    )
    message: str = Field(..., description="Human-readable error message")


class ReportGenerationError(BaseModel):
    """Wrapper for report generation error response."""
    error: ReportGenerationErrorDetail
