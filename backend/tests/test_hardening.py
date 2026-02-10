"""
Phase 7 Hardening Tests

Verifies:
- Rate limiting functionality
- Request timeout handling
- Caching behavior
- Error handling and graceful degradation
- Environment validation
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio

from fastapi.testclient import TestClient
from app.main import app
from app.utils.hardening import (
    analysis_cache,
    limiter,
    validate_environment,
    get_cached_analysis,
    cache_analysis,
    generate_request_id,
)


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
    mock.executive_summary = "Test summary."
    mock.strengths = ["Good docs"]
    mock.improvements = ["Add tests"]
    mock.resume_bullets = ["Built test-repo"]
    
    mock.rule_evaluation = MagicMock()
    mock.rule_evaluation.documentation_score = 8
    mock.rule_evaluation.structure_score = 7
    mock.rule_evaluation.configuration_score = 9
    mock.rule_evaluation.completeness_score = 6
    
    mock.ai_insights = MagicMock()
    mock.ai_insights.summary = "Fallback"
    mock.ai_insights.strengths = ["Fallback"]
    mock.ai_insights.improvements = ["Fallback"]
    
    return mock


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_response_format(self):
        """Verify rate limit error has user-friendly format."""
        # Make requests until rate limited (configured as 10/minute)
        responses = []
        for i in range(12):
            analysis_cache.clear()  # Clear cache to force new analysis
            response = client.post(
                "/api/v1/analyze",
                json={"repo_url": f"https://github.com/owner/rate-test-{i}"}
            )
            responses.append(response)
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0, "Should hit rate limit after many requests"
        
        # Check error format
        data = rate_limited[0].json()
        assert data["status"] == "error"
        assert "too many requests" in data["error"]["message"].lower()
        assert data["error"]["type"] == "RATE_LIMITED"
    
    def test_rate_limit_header(self):
        """Verify rate limited response includes request ID."""
        # Make enough requests to trigger rate limit
        for i in range(12):
            analysis_cache.clear()
            response = client.post(
                "/api/v1/analyze",
                json={"repo_url": f"https://github.com/owner/header-test-{i}"}
            )
            if response.status_code == 429:
                assert "X-Request-ID" in response.headers
                break


# ============================================================================
# Caching Tests
# ============================================================================

class TestCaching:
    """Test in-memory caching functionality."""
    
    def test_cache_hit_returns_cached_result(self):
        """Verify second request returns cached result."""
        test_url = "https://github.com/owner/cache-test"
        test_result = {"status": "success", "repo_name": "cache-test"}
        
        # Cache a result
        cache_analysis(test_url, test_result)
        
        # Verify cache hit
        cached = get_cached_analysis(test_url)
        assert cached == test_result
    
    def test_cache_miss_returns_none(self):
        """Verify cache miss returns None."""
        cached = get_cached_analysis("https://github.com/owner/not-cached")
        assert cached is None
    
    @patch('app.api.analyze.AnalysisPipeline')
    def test_cached_response_skips_pipeline(self, mock_pipeline_class, mock_final_report):
        """Verify cached responses don't re-run the pipeline."""
        mock_instance = MagicMock()
        mock_instance.run_full_analysis = AsyncMock(return_value=mock_final_report)
        mock_pipeline_class.return_value = mock_instance
        
        test_url = "https://github.com/owner/pipeline-skip-test"
        
        # First request - runs pipeline
        response1 = client.post("/api/v1/analyze", json={"repo_url": test_url})
        assert response1.status_code == 200
        
        # Second request - should use cache
        response2 = client.post("/api/v1/analyze", json={"repo_url": test_url})
        assert response2.status_code == 200
        
        # Pipeline should only be called once
        assert mock_instance.run_full_analysis.call_count == 1


# ============================================================================
# Request ID Tests
# ============================================================================

class TestRequestTracking:
    """Test request ID generation and tracking."""
    
    def test_request_id_in_response_headers(self):
        """Verify all responses include X-Request-ID header."""
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 8
    
    def test_unique_request_ids(self):
        """Verify each request gets unique ID."""
        ids = set()
        for _ in range(10):
            response = client.get("/")
            ids.add(response.headers["X-Request-ID"])
        
        assert len(ids) == 10, "All request IDs should be unique"
    
    def test_generate_request_id_format(self):
        """Verify request ID format."""
        request_id = generate_request_id()
        assert len(request_id) == 8
        assert request_id.isalnum() or "-" in request_id


# ============================================================================
# Environment Validation Tests
# ============================================================================

class TestEnvironmentValidation:
    """Test startup environment validation."""
    
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key', 'GITHUB_TOKEN': 'test-token'})
    def test_valid_environment_no_warnings(self):
        """Verify no warnings when all keys are set."""
        warnings = validate_environment()
        assert "GEMINI_API_KEY not configured" not in warnings
        assert "GITHUB_TOKEN not configured" not in warnings
    
    @patch.dict('os.environ', {'GEMINI_API_KEY': '', 'GITHUB_TOKEN': ''}, clear=True)
    def test_missing_keys_generate_warnings(self):
        """Verify warnings are generated for missing keys."""
        warnings = validate_environment()
        assert any("GEMINI_API_KEY" in w for w in warnings)


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestGracefulDegradation:
    """Test graceful error handling."""
    
    def test_invalid_url_friendly_error(self):
        """Verify invalid URL returns friendly error."""
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "not-a-url"}
        )
        
        # Should return 400 with friendly message
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "valid" in data["error"]["message"].lower()
    
    def test_no_stack_traces_in_errors(self):
        """Verify no stack traces are exposed in error responses."""
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": "invalid"}
        )
        
        data = response.json()
        error_message = str(data)
        
        assert "Traceback" not in error_message
        assert "File \"" not in error_message
        assert "line " not in error_message.lower() or "try again" in error_message.lower()


# ============================================================================
# Request Body Size Tests
# ============================================================================

class TestRequestBodyLimits:
    """Test request body size limits."""
    
    def test_large_body_rejected(self):
        """Verify excessively large request bodies are rejected."""
        # Create a payload larger than 1MB
        large_url = "https://github.com/owner/" + "x" * (1024 * 1024 + 100)
        
        response = client.post(
            "/api/v1/analyze",
            json={"repo_url": large_url}
        )
        
        # Should be rejected (either 413 or 422 for validation)
        assert response.status_code in [413, 422]


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthEndpoint:
    """Test health check endpoint for demo readiness."""
    
    def test_health_endpoint_responds(self):
        """Verify health endpoint is available."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_root_endpoint_responds(self):
        """Verify root endpoint provides API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "docs" in data
