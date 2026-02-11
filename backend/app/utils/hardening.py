"""
Hardening Utilities Module

Phase 7: Shared utilities for rate limiting, caching, and logging.
Separated to avoid circular imports between main.py and API endpoints.
"""

import os
import uuid
import logging
from cachetools import TTLCache
from slowapi import Limiter
from slowapi.util import get_remote_address

# ============================================================================
# Configuration Constants (Phase 7 Hardening)
# ============================================================================

# Rate limiting: requests per minute per IP
RATE_LIMIT = os.getenv("RATE_LIMIT", "10/minute")

# Request timeout in seconds (overall pipeline timeout)
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "90"))

# Maximum request body size (1MB)
MAX_REQUEST_BODY_SIZE = int(os.getenv("MAX_REQUEST_BODY_SIZE", "1048576"))

# CORS allowed origins (supports FRONTEND_URL for production or comma-separated list)
FRONTEND_URL = os.getenv("FRONTEND_URL")
if FRONTEND_URL:
    # Production: Use FRONTEND_URL
    CORS_ORIGINS = [FRONTEND_URL.rstrip("/")]
else:
    # Development: Use CORS_ORIGINS or default to localhost
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

# Cache TTL in seconds (15 minutes)
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "900"))

# Cache max size (max cached responses)
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "100"))

# ============================================================================
# Logging Configuration
# ============================================================================

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gitinsight")

# ============================================================================
# Rate Limiter Setup
# ============================================================================

limiter = Limiter(key_func=get_remote_address)

# ============================================================================
# In-Memory Cache for Analysis Results
# ============================================================================

# Simple TTL cache: key = repo_url, value = response dict
analysis_cache: TTLCache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS)


def get_cached_analysis(repo_url: str) -> dict | None:
    """Get cached analysis result if available."""
    return analysis_cache.get(repo_url)


def cache_analysis(repo_url: str, result: dict) -> None:
    """Cache analysis result for future requests."""
    analysis_cache[repo_url] = result


def generate_request_id() -> str:
    """Generate a unique request ID for tracing."""
    return str(uuid.uuid4())[:8]


def validate_environment() -> list[str]:
    """
    Validate required environment variables on startup.
    Returns list of warnings (non-fatal) and raises for critical issues.
    """
    warnings = []
    
    # GEMINI_API_KEY is required for AI analysis
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.warning("GEMINI_API_KEY not set - AI analysis will fail")
        warnings.append("GEMINI_API_KEY not configured")
    
    # GITHUB_TOKEN is optional but recommended
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.info("GITHUB_TOKEN not set - using unauthenticated GitHub API (lower rate limits)")
        warnings.append("GITHUB_TOKEN not configured (rate limits may apply)")
    
    return warnings
