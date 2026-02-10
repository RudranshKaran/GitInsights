"""
Full Analysis API Endpoint

This module provides the /analyze endpoint for running
the complete evaluation pipeline including AI analysis.

Phase 6: Frontend Integration Support.
Phase 7: Rate limiting, caching, and hardened error handling.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.schemas.models import (
    IngestErrorDetail,
    FinalReport,
)
from app.pipelines.analysis_pipeline import AnalysisPipeline, PipelineError
from app.utils.hardening import limiter, get_cached_analysis, cache_analysis, logger


router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request model for full analysis."""
    repo_url: str = Field(..., description="Public GitHub repository URL", max_length=500)


def format_frontend_response(report: FinalReport) -> dict:
    """
    Format FinalReport for frontend consumption.
    
    Consolidates report data into the structure expected by Phase 6 UI.
    Does NOT expose raw JSON or internal phase details.
    """
    return {
        "status": "success",
        "repo_name": report.repo_name,
        "final_score": report.overall_score,
        "report": {
            "summary": report.executive_summary or report.ai_insights.summary,
            "strengths": report.strengths or report.ai_insights.strengths[:5],
            "improvements": report.improvements or report.ai_insights.improvements[:5],
            "resume_bullets": report.resume_bullets,
        },
        "section_scores": {
            "documentation": report.rule_evaluation.documentation_score,
            "structure": report.rule_evaluation.structure_score,
            "configuration": report.rule_evaluation.configuration_score,
            "completeness": report.rule_evaluation.completeness_score,
        },
        "error": None,
    }


def get_user_friendly_message(error_type: str) -> str:
    """
    Map technical error types to user-friendly messages.
    
    Messages are calm, actionable, and non-technical.
    """
    messages = {
        "INVALID_URL": "Please enter a valid GitHub repository URL.",
        "PRIVATE_REPO": "This repository appears to be private. Please try a public repository.",
        "NOT_FOUND": "We couldn't find this repository. Please check the URL and try again.",
        "RATE_LIMITED": "We're experiencing high demand. Please try again in a few minutes.",
        "CONFIGURATION_ERROR": "We couldn't analyze this repository right now. Please try again later.",
        "TIMEOUT": "The analysis is taking too long. Please try again with a smaller repository.",
        "UNKNOWN": "An unexpected error occurred. Please try again.",
    }
    return messages.get(error_type, messages["UNKNOWN"])


@router.post(
    "/analyze",
    responses={
        200: {"description": "Successful analysis"},
        400: {"description": "Invalid URL"},
        403: {"description": "Private repository"},
        404: {"description": "Repository not found"},
        429: {"description": "Rate limited"},
        500: {"description": "Analysis failed"},
        504: {"description": "Request timeout"},
    },
    summary="Analyze GitHub Repository",
    description="Run full analysis pipeline including AI evaluation and report generation."
)
@limiter.limit("10/minute")
async def analyze_repository(request: Request, body: AnalyzeRequest):
    """
    Run full analysis pipeline on a GitHub repository.
    
    This endpoint performs complete evaluation:
    1. Repository ingestion (Phase 1)
    2. Rule-based evaluation (Phase 2)
    3. AI-assisted analysis (Phase 3)
    4. Hybrid scoring (Phase 4)
    5. Report generation (Phase 5)
    
    Returns a frontend-ready response for Phase 6 UI rendering.
    No internal phase names or implementation details are exposed.
    
    Phase 7: Includes rate limiting and result caching.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    repo_url = body.repo_url.strip()
    
    # Check cache first
    cached_result = get_cached_analysis(repo_url)
    if cached_result:
        logger.info(f"[{request_id}] Cache hit for {repo_url}")
        return JSONResponse(status_code=200, content=cached_result)
    
    logger.info(f"[{request_id}] Starting analysis for {repo_url}")
    
    try:
        pipeline = AnalysisPipeline()
        report = await pipeline.run_full_analysis(repo_url)
        
        result = format_frontend_response(report)
        
        # Cache successful results
        cache_analysis(repo_url, result)
        logger.info(f"[{request_id}] Analysis completed and cached for {repo_url}")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except PipelineError as e:
        logger.warning(f"[{request_id}] Pipeline error: {e.error_type} - {e.message}")
        
        status_code_map = {
            "INVALID_URL": 400,
            "PRIVATE_REPO": 403,
            "NOT_FOUND": 404,
            "RATE_LIMITED": 429,
            "CONFIGURATION_ERROR": 500,
            "UNKNOWN": 500,
        }
        
        status_code = status_code_map.get(e.error_type, 500)
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "repo_name": None,
                "final_score": None,
                "report": None,
                "section_scores": None,
                "error": {
                    "type": e.error_type,
                    "message": get_user_friendly_message(e.error_type),
                },
            }
        )
        
    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error: {type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "repo_name": None,
                "final_score": None,
                "report": None,
                "section_scores": None,
                "error": {
                    "type": "UNKNOWN",
                    "message": get_user_friendly_message("UNKNOWN"),
                },
            }
        )
