"""
Tests for the /analyze endpoint (Phase 6 Frontend Integration)

Verifies:
- Frontend-ready response format
- User-friendly error messages
- Status field for state management
- No internal phase details exposed

Phase 7: Tests adapted for rate limiting and caching.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient
from app.main import app
from app.pipelines.analysis_pipeline import PipelineError
from app.utils.hardening import analysis_cache, limiter


client = TestClient(app)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clear_cache_and_limits():
    """Clear cache and reset rate limits before each test."""
    analysis_cache.clear()
    limiter.reset()
    yield
    analysis_cache.clear()


@pytest.fixture
def mock_final_report():
    """Create a mock FinalReport object."""
    mock = MagicMock()
    mock.repo_name = "test-repo"
    mock.overall_score = 75.0
    mock.executive_summary = "Test summary for the repository."
    mock.strengths = ["Good documentation", "Clean structure"]
    mock.improvements = ["Add tests", "Improve README"]
    mock.resume_bullets = ["Built test-repo using Python"]
    
    mock.rule_evaluation = MagicMock()
    mock.rule_evaluation.documentation_score = 8
    mock.rule_evaluation.structure_score = 7
    mock.rule_evaluation.configuration_score = 9
    mock.rule_evaluation.completeness_score = 6
    
    mock.ai_insights = MagicMock()
    mock.ai_insights.summary = "Fallback summary"
    mock.ai_insights.strengths = ["Fallback strength"]
    mock.ai_insights.improvements = ["Fallback improvement"]
    
    return mock


# ============================================================================
# Success Response Tests
# ============================================================================

class TestSuccessResponse:
    """Test successful analysis responses."""
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_success_response_structure(self, mock_pipeline_class, mock_final_report):
        """Verify success response has correct frontend structure."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(return_value=mock_final_report)
        mock_pipeline_class.return_value = mock_instance
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "https://github.com/owner/repo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields for frontend
        assert data["status"] == "success"
        assert data["repo_name"] == "test-repo"
        assert data["final_score"] == 75.0
        assert data["error"] is None
        
        # Verify report structure
        assert "report" in data
        assert "summary" in data["report"]
        assert "strengths" in data["report"]
        assert "improvements" in data["report"]
        assert "resume_bullets" in data["report"]
        
        # Verify section scores
        assert "section_scores" in data
        assert data["section_scores"]["documentation"] == 8
        assert data["section_scores"]["structure"] == 7
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_no_internal_details_exposed(self, mock_pipeline_class, mock_final_report):
        """Verify no internal phase names or implementation details are exposed."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(return_value=mock_final_report)
        mock_pipeline_class.return_value = mock_instance
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "https://github.com/owner/repo"}
        )
        
        response_text = response.text.lower()
        
        # No internal phase names
        assert "phase" not in response_text
        assert "pipeline" not in response_text
        assert "ingestion" not in response_text
        assert "hybrid" not in response_text


# ============================================================================
# Error Response Tests
# ============================================================================

class TestErrorResponses:
    """Test error responses are user-friendly."""
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_invalid_url_error(self, mock_pipeline_class):
        """Test user-friendly message for invalid URL."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(
            side_effect=PipelineError("INVALID_URL", "Invalid URL", None)
        )
        mock_pipeline_class.return_value = mock_instance
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "not-a-url"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["status"] == "error"
        assert data["error"]["type"] == "INVALID_URL"
        assert "valid GitHub repository URL" in data["error"]["message"]
        
        # No technical details
        assert "stack" not in data["error"]["message"].lower()
        assert "exception" not in data["error"]["message"].lower()
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_private_repo_error(self, mock_pipeline_class):
        """Test user-friendly message for private repository."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(
            side_effect=PipelineError("PRIVATE_REPO", "Private repo", None)
        )
        mock_pipeline_class.return_value = mock_instance
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "https://github.com/owner/private-repo"}
        )
        
        assert response.status_code == 403
        data = response.json()
        
        assert data["status"] == "error"
        assert "private" in data["error"]["message"].lower()
        assert "public repository" in data["error"]["message"].lower()
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_not_found_error(self, mock_pipeline_class):
        """Test user-friendly message for repository not found."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(
            side_effect=PipelineError("NOT_FOUND", "Not found", None)
        )
        mock_pipeline_class.return_value = mock_instance
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "https://github.com/owner/nonexistent"}
        )
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["status"] == "error"
        assert "couldn't find" in data["error"]["message"].lower()
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_rate_limit_error(self, mock_pipeline_class):
        """Test user-friendly message for rate limiting."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(
            side_effect=PipelineError("RATE_LIMITED", "Rate limited", None)
        )
        mock_pipeline_class.return_value = mock_instance
        
        # Use unique URL to avoid cache hit
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "https://github.com/owner/rate-limit-test"}
        )
        
        assert response.status_code == 429
        data = response.json()
        
        assert data["status"] == "error"
        assert "try again" in data["error"]["message"].lower()
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_unknown_error_is_friendly(self, mock_pipeline_class):
        """Test that unknown errors still produce friendly messages."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(
            side_effect=Exception("Internal server error with stack trace")
        )
        mock_pipeline_class.return_value = mock_instance
        
        # Use unique URL to avoid cache hit
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "https://github.com/owner/unknown-error-test"}
        )
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["status"] == "error"
        # Should not contain the actual exception message
        assert "stack trace" not in data["error"]["message"]
        assert "try again" in data["error"]["message"].lower()


# ============================================================================
# Response Structure Tests
# ============================================================================

class TestResponseStructure:
    """Test response structure for frontend state management."""
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_success_has_null_error(self, mock_pipeline_class, mock_final_report):
        """Success responses should have null error field."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(return_value=mock_final_report)
        mock_pipeline_class.return_value = mock_instance
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "https://github.com/owner/repo"}
        )
        
        data = response.json()
        assert data["error"] is None
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_error_has_null_report(self, mock_pipeline_class):
        """Error responses should have null report field."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(
            side_effect=PipelineError("INVALID_URL", "Invalid", None)
        )
        mock_pipeline_class.return_value = mock_instance
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "bad"}
        )
        
        data = response.json()
        assert data["report"] is None
        assert data["section_scores"] is None
        assert data["final_score"] is None


# ============================================================================
# Frontend State Determinism Tests
# ============================================================================

class TestStateDeterminism:
    """Test that same backend response produces same frontend state."""
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_same_input_same_output(self, mock_pipeline_class, mock_final_report):
        """Verify deterministic responses for same input.
        
        Phase 7: With caching enabled, second request returns cached result.
        This is the expected deterministic behavior.
        """
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(return_value=mock_final_report)
        mock_pipeline_class.return_value = mock_instance
        
        # Use unique URL for this test
        test_url = "https://github.com/owner/determinism-test"
        
        response1 = client.post(
            "/api/v1/analyze",
            json={"repo_url": test_url}
        )
        
        response2 = client.post(
            "/api/v1/analyze",
            json={"repo_url": test_url}
        )
        
        # Both responses should be identical (second from cache)
        assert response1.json() == response2.json()
        assert response1.status_code == 200
        assert response2.status_code == 200
