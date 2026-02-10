"""
Health Check Endpoint

Provides a simple health check endpoint to verify the API is running.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns a simple status response to verify the API is operational.
    
    Returns:
        dict: A dictionary with status "ok"
    """
    return {"status": "ok"}
