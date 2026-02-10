"""
Repository Ingestion API Endpoints

This module provides the /ingest endpoint for converting
GitHub repository URLs into structured data.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.models import (
    IngestRequest,
    IngestSuccessResponse,
    IngestErrorResponse,
    IngestErrorDetail,
    FileEntryResponse,
)
from app.services.ingestion_service import (
    IngestionService,
    IngestedRepository,
    IngestionError,
)


router = APIRouter()


@router.post(
    "/ingest",
    response_model=IngestSuccessResponse,
    responses={
        400: {"model": IngestErrorResponse, "description": "Invalid URL"},
        403: {"model": IngestErrorResponse, "description": "Private repository"},
        404: {"model": IngestErrorResponse, "description": "Repository not found"},
        429: {"model": IngestErrorResponse, "description": "Rate limited"},
        500: {"model": IngestErrorResponse, "description": "Unknown error"},
    },
    summary="Ingest GitHub Repository",
    description="Convert a GitHub repository URL into structured, deterministic data. No AI processing."
)
async def ingest_repository(request: IngestRequest) -> IngestSuccessResponse | JSONResponse:
    """
    Ingest a GitHub repository and return structured data.
    
    This endpoint performs deterministic data extraction:
    1. Validates the GitHub URL
    2. Checks repository accessibility
    3. Fetches repository metadata
    4. Fetches complete file tree
    5. Fetches README content (if present)
    6. Detects language breakdown
    
    No AI reasoning, scoring, or interpretation is performed.
    Same input always produces the same output.
    
    Args:
        request: IngestRequest containing github_url
        
    Returns:
        IngestSuccessResponse with structured repository data
        or IngestErrorResponse on failure
    """
    service = IngestionService()
    result = await service.ingest(request.github_url)
    
    if isinstance(result, IngestionError):
        # Map error types to HTTP status codes
        status_code_map = {
            "INVALID_URL": 400,
            "PRIVATE_REPO": 403,
            "NOT_FOUND": 404,
            "RATE_LIMITED": 429,
            "UNKNOWN": 500,
        }
        
        status_code = status_code_map.get(result.error_type, 500)
        
        error_response = IngestErrorResponse(
            error=IngestErrorDetail(
                type=result.error_type,
                message=result.message,
                details=result.details
            )
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump()
        )
    
    # Convert to response model
    files = [
        FileEntryResponse(
            path=f["path"],
            name=f["name"],
            extension=f["extension"],
            type=f["type"]
        )
        for f in result.files
    ]
    
    return IngestSuccessResponse(
        repo_name=result.repo_name,
        owner=result.owner,
        default_branch=result.default_branch,
        languages=result.languages,
        files=files,
        readme=result.readme
    )
