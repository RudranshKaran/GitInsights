"""
Repository Evaluation API Endpoints

This module provides the /evaluate endpoint for running
deterministic rule-based evaluation on repository data.

Phase 2: Zero AI dependency.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.models import (
    IngestRequest,
    IngestErrorResponse,
    IngestErrorDetail,
    RuleEvaluationResult,
)
from app.services.ingestion_service import (
    IngestionService,
    IngestionError,
)
from app.services.evaluation_service import (
    EvaluationService,
    get_evaluation_service,
)


router = APIRouter()


# Response model for evaluation
class EvaluateSuccessResponse(RuleEvaluationResult):
    """Successful evaluation response matching Phase 2 output schema."""
    pass


@router.post(
    "/evaluate",
    response_model=EvaluateSuccessResponse,
    responses={
        400: {"model": IngestErrorResponse, "description": "Invalid URL"},
        403: {"model": IngestErrorResponse, "description": "Private repository"},
        404: {"model": IngestErrorResponse, "description": "Repository not found"},
        429: {"model": IngestErrorResponse, "description": "Rate limited"},
        500: {"model": IngestErrorResponse, "description": "Evaluation failed"},
    },
    summary="Evaluate GitHub Repository",
    description="Evaluate a GitHub repository using deterministic rule-based analysis. Zero AI dependency."
)
async def evaluate_repository(request: IngestRequest) -> EvaluateSuccessResponse | JSONResponse:
    """
    Evaluate a GitHub repository using rule-based analysis.
    
    This endpoint performs deterministic evaluation:
    1. Ingests repository data (Phase 1)
    2. Applies rule-based evaluation (Phase 2)
    3. Returns scores and issues
    
    Hard Constraints:
    - No AI reasoning or inference
    - No probabilistic logic
    - Same input always produces the same output
    - All scores derived from explicit conditions
    
    Args:
        request: IngestRequest containing github_url
        
    Returns:
        EvaluateSuccessResponse with scores and issues
        or IngestErrorResponse on failure
    """
    # Step 1: Ingest repository data
    ingestion_service = IngestionService()
    ingestion_result = await ingestion_service.ingest(request.github_url)
    
    if isinstance(ingestion_result, IngestionError):
        # Map error types to HTTP status codes
        status_code_map = {
            "INVALID_URL": 400,
            "PRIVATE_REPO": 403,
            "NOT_FOUND": 404,
            "RATE_LIMITED": 429,
            "UNKNOWN": 500,
        }
        
        status_code = status_code_map.get(ingestion_result.error_type, 500)
        
        error_response = IngestErrorResponse(
            error=IngestErrorDetail(
                type=ingestion_result.error_type,
                message=ingestion_result.message,
                details=ingestion_result.details,
            )
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump()
        )
    
    # Step 2: Run rule-based evaluation
    evaluation_service = get_evaluation_service()
    evaluation_result = evaluation_service.evaluate(ingestion_result)
    
    # Return evaluation response
    return EvaluateSuccessResponse(
        documentation_score=evaluation_result.documentation_score,
        structure_score=evaluation_result.structure_score,
        configuration_score=evaluation_result.configuration_score,
        completeness_score=evaluation_result.completeness_score,
        issues=evaluation_result.issues,
    )
