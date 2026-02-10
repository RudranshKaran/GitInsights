"""
GitHub API Client Service

This module provides async methods for interacting with the GitHub REST API.
All operations are deterministic with explicit error handling.
No AI reasoning or interpretation.

Phase 7: Includes retry logic with exponential backoff for transient failures.
"""

import os
import logging
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

# Configure logger
logger = logging.getLogger("gitinsight.github")

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

# Maximum file count to prevent overwhelming large repositories
MAX_FILE_COUNT = 5000

# Maximum recursion depth for file tree
MAX_TREE_DEPTH = 10

# Retry configuration
MAX_RETRIES = 3
MIN_RETRY_WAIT = 1  # seconds
MAX_RETRY_WAIT = 10  # seconds


class RetryableGitHubError(Exception):
    """Exception for retryable GitHub API errors (rate limits, server errors)."""
    pass


@dataclass
class GitHubError:
    """Represents a GitHub API error with structured details."""
    error_type: str
    message: str
    details: str | None = None
    
    def to_dict(self) -> dict:
        """Convert error to dictionary format."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "details": self.details
            }
        }


@dataclass
class RepositoryMetadata:
    """Repository metadata from GitHub API."""
    name: str
    owner: str
    default_branch: str
    size: int | None
    primary_language: str | None


@dataclass
class FileEntry:
    """Represents a file or directory in the repository."""
    path: str
    name: str
    extension: str | None
    type: str  # "file" or "directory"


class GitHubClient:
    """
    Async client for GitHub REST API operations.
    
    This client handles all GitHub API interactions with proper
    error handling, rate limit awareness, and retry logic.
    
    Phase 7: Includes exponential backoff retry for transient failures.
    """
    
    def __init__(self, token: str | None = None):
        """
        Initialize the GitHub client.
        
        Args:
            token: Optional GitHub personal access token for higher rate limits
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitInsight-Bot/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT, max=MAX_RETRY_WAIT),
        retry=retry_if_exception_type(RetryableGitHubError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _make_request_with_retry(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> tuple[dict | list | str | None, GitHubError | None]:
        """
        Make an HTTP request to GitHub API with retry logic.
        
        Retries on:
        - Rate limiting (429)
        - Server errors (5xx)
        - Network timeouts
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for httpx
            
        Returns:
            Tuple of (response_data, error)
            
        Raises:
            RetryableGitHubError: For transient failures that should be retried
        """
        return await self._make_request_internal(method, url, **kwargs)
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> tuple[dict | list | str | None, GitHubError | None]:
        """
        Make an HTTP request to GitHub API with automatic retry.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for httpx
            
        Returns:
            Tuple of (response_data, error)
        """
        try:
            return await self._make_request_with_retry(method, url, **kwargs)
        except RetryableGitHubError as e:
            # All retries exhausted, return the error
            logger.error(f"All retries exhausted for {url}: {e}")
            return None, GitHubError(
                error_type="RATE_LIMITED",
                message="GitHub API is temporarily unavailable",
                details=str(e)
            )
        except Exception as e:
            logger.exception(f"Unexpected error in _make_request: {e}")
            return None, GitHubError(
                error_type="UNKNOWN",
                message="Unexpected error occurred",
                details=str(e)
            )
    
    async def _make_request_internal(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> tuple[dict | list | str | None, GitHubError | None]:
        """
        Internal request method that performs the actual HTTP call.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for httpx
            
        Returns:
            Tuple of (response_data, error)
            
        Raises:
            RetryableGitHubError: For transient failures that should be retried
        """
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self.headers,
                    **kwargs
                )
                
                # Handle different status codes
                if response.status_code == 200:
                    # Check content type for raw content requests
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        return response.json(), None
                    else:
                        return response.text, None
                
                elif response.status_code == 404:
                    return None, GitHubError(
                        error_type="NOT_FOUND",
                        message="Repository not found",
                        details="The repository does not exist or has been deleted"
                    )
                
                elif response.status_code == 403:
                    # Check if it's rate limiting - this is retryable
                    if "rate limit" in response.text.lower():
                        remaining = response.headers.get("X-RateLimit-Remaining", "0")
                        reset_time = response.headers.get("X-RateLimit-Reset", "unknown")
                        raise RetryableGitHubError(
                            f"Rate limited: Remaining={remaining}, Reset={reset_time}"
                        )
                    else:
                        return None, GitHubError(
                            error_type="PRIVATE_REPO",
                            message="Repository is not accessible",
                            details="The repository may be private or you lack permissions"
                        )
                
                elif response.status_code == 401:
                    return None, GitHubError(
                        error_type="PRIVATE_REPO",
                        message="Authentication required",
                        details="The repository requires authentication to access"
                    )
                
                elif response.status_code == 429:
                    # Rate limited - retryable
                    raise RetryableGitHubError("Too many requests - rate limit exceeded")
                
                elif response.status_code >= 500:
                    # Server errors are retryable
                    raise RetryableGitHubError(
                        f"GitHub server error: {response.status_code}"
                    )
                
                else:
                    return None, GitHubError(
                        error_type="UNKNOWN",
                        message=f"Unexpected status code: {response.status_code}",
                        details=response.text[:200] if response.text else None
                    )
                    
        except httpx.TimeoutException:
            # Timeouts are retryable
            raise RetryableGitHubError(
                f"Request timed out after {REQUEST_TIMEOUT} seconds"
            )
        except httpx.RequestError as e:
            # Network errors are retryable
            raise RetryableGitHubError(f"Network error: {e}")
        except RetryableGitHubError:
            # Re-raise retryable errors for the retry decorator
            raise
        except Exception as e:
            # Non-retryable unexpected errors
            logger.exception(f"Unexpected error in GitHub request: {e}")
            return None, GitHubError(
                error_type="UNKNOWN",
                message="Unexpected error occurred",
                details=str(e)
            )
    
    async def get_repository_metadata(
        self, 
        owner: str, 
        repo: str
    ) -> tuple[RepositoryMetadata | None, GitHubError | None]:
        """
        Fetch repository metadata from GitHub API.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            
        Returns:
            Tuple of (RepositoryMetadata, error)
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        data, error = await self._make_request("GET", url)
        
        if error:
            return None, error
        
        if not isinstance(data, dict):
            return None, GitHubError(
                error_type="UNKNOWN",
                message="Invalid response format",
                details="Expected JSON object from repository endpoint"
            )
        
        return RepositoryMetadata(
            name=data.get("name", repo),
            owner=data.get("owner", {}).get("login", owner),
            default_branch=data.get("default_branch", "main"),
            size=data.get("size"),
            primary_language=data.get("language")
        ), None
    
    async def get_repository_tree(
        self, 
        owner: str, 
        repo: str, 
        branch: str
    ) -> tuple[list[FileEntry] | None, GitHubError | None]:
        """
        Fetch complete file tree using GitHub Trees API.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            branch: Branch name to fetch tree from
            
        Returns:
            Tuple of (list of FileEntry, error)
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        data, error = await self._make_request("GET", url)
        
        if error:
            return None, error
        
        if not isinstance(data, dict):
            return None, GitHubError(
                error_type="UNKNOWN",
                message="Invalid response format",
                details="Expected JSON object from tree endpoint"
            )
        
        tree = data.get("tree", [])
        truncated = data.get("truncated", False)
        
        if truncated:
            return None, GitHubError(
                error_type="UNKNOWN",
                message="Repository too large",
                details="File tree was truncated due to repository size"
            )
        
        if len(tree) > MAX_FILE_COUNT:
            return None, GitHubError(
                error_type="UNKNOWN",
                message="Repository exceeds file limit",
                details=f"Repository has {len(tree)} files, maximum is {MAX_FILE_COUNT}"
            )
        
        files = []
        for item in tree:
            path = item.get("path", "")
            name = path.split("/")[-1] if path else ""
            item_type = item.get("type", "")
            
            # Determine file extension
            extension = None
            if item_type == "blob" and "." in name:
                extension = name.rsplit(".", 1)[-1]
            
            files.append(FileEntry(
                path=path,
                name=name,
                extension=extension,
                type="file" if item_type == "blob" else "directory"
            ))
        
        return files, None
    
    async def get_languages(
        self, 
        owner: str, 
        repo: str
    ) -> tuple[dict[str, int] | None, GitHubError | None]:
        """
        Fetch repository language breakdown.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            
        Returns:
            Tuple of (language dict, error)
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages"
        data, error = await self._make_request("GET", url)
        
        if error:
            return None, error
        
        if not isinstance(data, dict):
            return None, GitHubError(
                error_type="UNKNOWN",
                message="Invalid response format",
                details="Expected JSON object from languages endpoint"
            )
        
        return data, None
    
    async def get_readme(
        self, 
        owner: str, 
        repo: str
    ) -> tuple[str | None, GitHubError | None]:
        """
        Fetch README content from repository.
        
        Tries multiple README formats: README.md, README.txt, README.rst
        
        Args:
            owner: Repository owner username
            repo: Repository name
            
        Returns:
            Tuple of (readme content string or None, error)
        """
        # Try to get README using GitHub's readme endpoint
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    url,
                    headers={
                        **self.headers,
                        "Accept": "application/vnd.github.raw+json"
                    }
                )
                
                if response.status_code == 200:
                    return response.text, None
                elif response.status_code == 404:
                    # No README found - this is not an error
                    return None, None
                elif response.status_code == 403:
                    if "rate limit" in response.text.lower():
                        return None, GitHubError(
                            error_type="RATE_LIMITED",
                            message="GitHub API rate limit exceeded",
                            details="Cannot fetch README"
                        )
                    return None, None
                else:
                    # Other errors - return None without error
                    return None, None
                    
            except httpx.TimeoutException:
                return None, GitHubError(
                    error_type="UNKNOWN",
                    message="Request timed out",
                    details="Could not fetch README within timeout"
                )
            except httpx.RequestError as e:
                return None, GitHubError(
                    error_type="UNKNOWN",
                    message="Network error",
                    details=str(e)
                )
    
    async def check_repository_exists(
        self, 
        owner: str, 
        repo: str
    ) -> tuple[bool, GitHubError | None]:
        """
        Check if a repository exists and is accessible.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            
        Returns:
            Tuple of (exists boolean, error if any)
        """
        metadata, error = await self.get_repository_metadata(owner, repo)
        
        if error:
            return False, error
        
        return True, None
