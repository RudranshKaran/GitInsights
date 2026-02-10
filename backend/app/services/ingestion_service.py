"""
Repository Ingestion Service

This module orchestrates the complete repository ingestion pipeline.
It converts a GitHub URL into structured, deterministic data.
No AI reasoning, scoring, or interpretation.
"""

from dataclasses import dataclass
from typing import Any

from app.services.github_client import GitHubClient, GitHubError, FileEntry
from app.utils.url_parser import parse_github_url, ParsedGitHubURL, URLParseError


@dataclass
class IngestedRepository:
    """
    Complete ingested repository data.
    
    This matches the output schema specified in Phase 1 requirements.
    """
    repo_name: str
    owner: str
    default_branch: str
    languages: dict[str, int]
    files: list[dict[str, Any]]
    readme: str | None
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching the output schema."""
        return {
            "repo_name": self.repo_name,
            "owner": self.owner,
            "default_branch": self.default_branch,
            "languages": self.languages,
            "files": self.files,
            "readme": self.readme
        }


@dataclass
class IngestionError:
    """Structured error for ingestion failures."""
    error_type: str
    message: str
    details: str | None = None
    
    def to_dict(self) -> dict:
        """Convert to error response format."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "details": self.details
            }
        }


class IngestionService:
    """
    Repository Ingestion Engine.
    
    Converts a GitHub repository URL into clean, deterministic, structured data.
    Executes all steps in order with explicit error handling.
    """
    
    def __init__(self, github_token: str | None = None):
        """
        Initialize the ingestion service.
        
        Args:
            github_token: Optional GitHub token for higher rate limits
        """
        self.github_client = GitHubClient(token=github_token)
    
    async def ingest(self, github_url: str) -> IngestedRepository | IngestionError:
        """
        Execute the complete ingestion pipeline.
        
        Steps executed in order:
        1. Validate GitHub URL
        2. Check repository accessibility
        3. Fetch repository metadata
        4. Fetch file tree
        5. Fetch README (if present)
        6. Detect languages
        
        Args:
            github_url: The GitHub repository URL to ingest
            
        Returns:
            IngestedRepository on success, IngestionError on failure
        """
        
        # Step 1: Validate GitHub URL
        parse_result = parse_github_url(github_url)
        
        if isinstance(parse_result, URLParseError):
            return IngestionError(
                error_type=parse_result.error_type,
                message=parse_result.message,
                details=parse_result.details
            )
        
        owner = parse_result.owner
        repo = parse_result.repo_name
        
        # Step 2: Check repository accessibility
        exists, error = await self.github_client.check_repository_exists(owner, repo)
        
        if error:
            return self._convert_github_error(error)
        
        if not exists:
            return IngestionError(
                error_type="NOT_FOUND",
                message="Repository not found",
                details=f"Could not find repository: {owner}/{repo}"
            )
        
        # Step 3: Fetch repository metadata
        metadata, error = await self.github_client.get_repository_metadata(owner, repo)
        
        if error:
            return self._convert_github_error(error)
        
        if not metadata:
            return IngestionError(
                error_type="UNKNOWN",
                message="Failed to fetch repository metadata",
                details="No metadata returned from GitHub API"
            )
        
        # Step 4: Fetch file tree
        files, error = await self.github_client.get_repository_tree(
            owner, repo, metadata.default_branch
        )
        
        if error:
            return self._convert_github_error(error)
        
        if files is None:
            files = []
        
        # Step 5: Fetch README (if present)
        readme_content, error = await self.github_client.get_readme(owner, repo)
        
        if error:
            # README errors are not fatal - just log and continue
            readme_content = None
        
        # Step 6: Detect languages
        languages, error = await self.github_client.get_languages(owner, repo)
        
        if error:
            # Language detection errors are not fatal
            languages = {}
        
        if languages is None:
            languages = {}
        
        # Build file list in required format
        formatted_files = [
            {
                "path": f.path,
                "name": f.name,
                "extension": f.extension,
                "type": f.type
            }
            for f in files
        ]
        
        return IngestedRepository(
            repo_name=metadata.name,
            owner=metadata.owner,
            default_branch=metadata.default_branch,
            languages=languages,
            files=formatted_files,
            readme=readme_content
        )
    
    def _convert_github_error(self, error: GitHubError) -> IngestionError:
        """Convert GitHubError to IngestionError."""
        return IngestionError(
            error_type=error.error_type,
            message=error.message,
            details=error.details
        )


# Singleton instance for convenience
_ingestion_service: IngestionService | None = None


def get_ingestion_service(github_token: str | None = None) -> IngestionService:
    """
    Get or create the ingestion service instance.
    
    Args:
        github_token: Optional GitHub token
        
    Returns:
        IngestionService instance
    """
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService(github_token=github_token)
    return _ingestion_service
