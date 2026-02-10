"""
GitHub URL Parser Utility

This module provides deterministic URL parsing and validation
for GitHub repository URLs. No AI reasoning or interpretation.
"""

import re
from dataclasses import dataclass


@dataclass
class ParsedGitHubURL:
    """Represents a successfully parsed GitHub repository URL."""
    owner: str
    repo_name: str
    url: str


@dataclass
class URLParseError:
    """Represents a URL parsing error with structured details."""
    error_type: str
    message: str
    details: str | None = None


# Valid GitHub repository URL patterns
GITHUB_REPO_PATTERNS = [
    # HTTPS format: https://github.com/owner/repo
    r"^https?://github\.com/(?P<owner>[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?)/(?P<repo>[a-zA-Z0-9._\-]+?)(?:\.git)?/?$",
    # HTTPS format with tree/blob: https://github.com/owner/repo/tree/branch
    r"^https?://github\.com/(?P<owner>[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?)/(?P<repo>[a-zA-Z0-9._\-]+?)(?:/(?:tree|blob)/[^/]+.*)?$",
]

# Patterns that indicate invalid URL types
INVALID_URL_PATTERNS = [
    # User profile URL
    (r"^https?://github\.com/[a-zA-Z0-9\-]+/?$", "User profile URLs are not supported"),
    # Gist URL
    (r"^https?://gist\.github\.com/", "Gist URLs are not supported"),
    # GitHub API URL
    (r"^https?://api\.github\.com/", "GitHub API URLs are not supported"),
    # GitHub raw content
    (r"^https?://raw\.githubusercontent\.com/", "Raw content URLs are not supported"),
]


def parse_github_url(url: str) -> ParsedGitHubURL | URLParseError:
    """
    Parse and validate a GitHub repository URL.
    
    This function performs deterministic validation with no AI interpretation.
    It checks URL format and extracts owner/repo information.
    
    Args:
        url: The URL string to parse
        
    Returns:
        ParsedGitHubURL on success, URLParseError on failure
    """
    if not url or not isinstance(url, str):
        return URLParseError(
            error_type="INVALID_URL",
            message="URL must be a non-empty string",
            details=f"Received: {type(url).__name__}"
        )
    
    # Normalize URL: strip whitespace
    url = url.strip()
    
    # Check if it's a GitHub URL at all
    if not re.match(r"^https?://", url):
        return URLParseError(
            error_type="INVALID_URL",
            message="URL must start with http:// or https://",
            details=f"Received: {url[:50]}..."
        )
    
    if "github.com" not in url.lower() and "github" not in url.lower():
        return URLParseError(
            error_type="INVALID_URL",
            message="URL must be a GitHub repository URL",
            details="Only github.com repository URLs are supported"
        )
    
    # Check for known invalid URL patterns
    for pattern, error_message in INVALID_URL_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return URLParseError(
                error_type="INVALID_URL",
                message=error_message,
                details=f"URL: {url}"
            )
    
    # Try to match valid repository patterns
    for pattern in GITHUB_REPO_PATTERNS:
        match = re.match(pattern, url, re.IGNORECASE)
        if match:
            owner = match.group("owner")
            repo = match.group("repo")
            
            # Clean up repo name (remove .git suffix if present)
            repo = repo.rstrip("/")
            if repo.endswith(".git"):
                repo = repo[:-4]
            
            # Construct canonical URL
            canonical_url = f"https://github.com/{owner}/{repo}"
            
            return ParsedGitHubURL(
                owner=owner,
                repo_name=repo,
                url=canonical_url
            )
    
    # If no pattern matched, return error
    return URLParseError(
        error_type="INVALID_URL",
        message="Invalid GitHub repository URL format",
        details=f"URL does not match expected pattern: https://github.com/owner/repository"
    )


def validate_github_url(url: str) -> bool:
    """
    Quick validation check for GitHub URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    result = parse_github_url(url)
    return isinstance(result, ParsedGitHubURL)
