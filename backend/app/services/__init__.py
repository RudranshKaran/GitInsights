"""
Services Module

Contains business logic services for GitHub data fetching,
repository analysis, and other core operations.
"""

from app.services.ingestion_service import IngestionService, IngestedRepository, IngestionError
from app.services.evaluation_service import EvaluationService, EvaluationResult
from app.services.hybrid_scoring_service import HybridScoringService

# AIAnalysisService is imported lazily to avoid langchain dependency issues
# when running tests that don't require AI functionality
def get_ai_analysis_service():
    """Lazy import for AIAnalysisService."""
    from app.services.ai_analysis_service import AIAnalysisService
    return AIAnalysisService

__all__ = [
    "IngestionService",
    "IngestedRepository",
    "IngestionError",
    "EvaluationService",
    "EvaluationResult",
    "HybridScoringService",
    "get_ai_analysis_service",
]
