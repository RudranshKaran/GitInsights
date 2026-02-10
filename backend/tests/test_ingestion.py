"""
Unit Tests for Repository Ingestion

Tests cover all scenarios specified in Phase 1 requirements:
- Invalid GitHub URL
- Private repository
- Empty repository
- Repository without README
- Repository with deeply nested folders
- Large repositories (graceful failure)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.utils.url_parser import parse_github_url, ParsedGitHubURL, URLParseError
from app.services.github_client import (
    GitHubClient,
    GitHubError,
    RepositoryMetadata,
    FileEntry,
)
from app.services.ingestion_service import (
    IngestionService,
    IngestedRepository,
    IngestionError,
)


# ============================================================================
# URL Parser Tests
# ============================================================================

class TestURLParser:
    """Tests for GitHub URL parsing and validation."""
    
    def test_valid_https_url(self):
        """Test parsing a valid HTTPS GitHub URL."""
        result = parse_github_url("https://github.com/owner/repo")
        assert isinstance(result, ParsedGitHubURL)
        assert result.owner == "owner"
        assert result.repo_name == "repo"
        assert result.url == "https://github.com/owner/repo"
    
    def test_valid_url_with_git_suffix(self):
        """Test parsing URL with .git suffix."""
        result = parse_github_url("https://github.com/owner/repo.git")
        assert isinstance(result, ParsedGitHubURL)
        assert result.repo_name == "repo"
    
    def test_valid_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash."""
        result = parse_github_url("https://github.com/owner/repo/")
        assert isinstance(result, ParsedGitHubURL)
        assert result.repo_name == "repo"
    
    def test_valid_url_with_tree_branch(self):
        """Test parsing URL with tree/branch path."""
        result = parse_github_url("https://github.com/owner/repo/tree/main")
        assert isinstance(result, ParsedGitHubURL)
        assert result.repo_name == "repo"
    
    def test_invalid_empty_url(self):
        """Test that empty URL returns error."""
        result = parse_github_url("")
        assert isinstance(result, URLParseError)
        assert result.error_type == "INVALID_URL"
    
    def test_invalid_none_url(self):
        """Test that None URL returns error."""
        result = parse_github_url(None)
        assert isinstance(result, URLParseError)
        assert result.error_type == "INVALID_URL"
    
    def test_invalid_non_github_url(self):
        """Test that non-GitHub URL returns error."""
        result = parse_github_url("https://gitlab.com/owner/repo")
        assert isinstance(result, URLParseError)
        assert result.error_type == "INVALID_URL"
    
    def test_invalid_user_profile_url(self):
        """Test that user profile URL returns error."""
        result = parse_github_url("https://github.com/username")
        assert isinstance(result, URLParseError)
        assert result.error_type == "INVALID_URL"
        assert "profile" in result.message.lower()
    
    def test_invalid_gist_url(self):
        """Test that gist URL returns error."""
        result = parse_github_url("https://gist.github.com/user/abc123")
        assert isinstance(result, URLParseError)
        assert result.error_type == "INVALID_URL"
    
    def test_invalid_raw_content_url(self):
        """Test that raw content URL returns error."""
        result = parse_github_url("https://raw.githubusercontent.com/owner/repo/main/file.py")
        assert isinstance(result, URLParseError)
        assert result.error_type == "INVALID_URL"
    
    def test_http_url(self):
        """Test that HTTP (non-HTTPS) URL is accepted."""
        result = parse_github_url("http://github.com/owner/repo")
        assert isinstance(result, ParsedGitHubURL)
        assert result.owner == "owner"


# ============================================================================
# GitHub Client Tests
# ============================================================================

class TestGitHubClient:
    """Tests for GitHub API client."""
    
    @pytest.fixture
    def client(self):
        """Create a GitHub client instance."""
        return GitHubClient()
    
    @pytest.mark.asyncio
    async def test_get_metadata_success(self, client):
        """Test successful metadata fetch."""
        mock_response = {
            "name": "test-repo",
            "owner": {"login": "test-owner"},
            "default_branch": "main",
            "size": 1234,
            "language": "Python"
        }
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (mock_response, None)
            
            metadata, error = await client.get_repository_metadata("test-owner", "test-repo")
            
            assert error is None
            assert metadata is not None
            assert metadata.name == "test-repo"
            assert metadata.owner == "test-owner"
            assert metadata.default_branch == "main"
    
    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self, client):
        """Test metadata fetch for non-existent repo."""
        error = GitHubError(
            error_type="NOT_FOUND",
            message="Repository not found",
            details="404"
        )
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (None, error)
            
            metadata, err = await client.get_repository_metadata("owner", "nonexistent")
            
            assert metadata is None
            assert err is not None
            assert err.error_type == "NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_get_metadata_private_repo(self, client):
        """Test metadata fetch for private repo."""
        error = GitHubError(
            error_type="PRIVATE_REPO",
            message="Repository is not accessible",
            details="403"
        )
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (None, error)
            
            metadata, err = await client.get_repository_metadata("owner", "private-repo")
            
            assert metadata is None
            assert err is not None
            assert err.error_type == "PRIVATE_REPO"
    
    @pytest.mark.asyncio
    async def test_get_metadata_rate_limited(self, client):
        """Test metadata fetch when rate limited."""
        error = GitHubError(
            error_type="RATE_LIMITED",
            message="Rate limit exceeded",
            details="429"
        )
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (None, error)
            
            metadata, err = await client.get_repository_metadata("owner", "repo")
            
            assert metadata is None
            assert err is not None
            assert err.error_type == "RATE_LIMITED"
    
    @pytest.mark.asyncio
    async def test_get_tree_success(self, client):
        """Test successful file tree fetch."""
        mock_response = {
            "tree": [
                {"path": "README.md", "type": "blob"},
                {"path": "src", "type": "tree"},
                {"path": "src/main.py", "type": "blob"},
            ],
            "truncated": False
        }
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (mock_response, None)
            
            files, error = await client.get_repository_tree("owner", "repo", "main")
            
            assert error is None
            assert files is not None
            assert len(files) == 3
            assert files[0].name == "README.md"
            assert files[0].extension == "md"
            assert files[0].type == "file"
    
    @pytest.mark.asyncio
    async def test_get_tree_deeply_nested(self, client):
        """Test file tree with deeply nested folders."""
        nested_files = [
            {"path": f"level{i}/level{i+1}/level{i+2}/file.py", "type": "blob"}
            for i in range(8)
        ]
        
        mock_response = {
            "tree": nested_files,
            "truncated": False
        }
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (mock_response, None)
            
            files, error = await client.get_repository_tree("owner", "repo", "main")
            
            assert error is None
            assert files is not None
            assert len(files) == 8
    
    @pytest.mark.asyncio
    async def test_get_tree_truncated_large_repo(self, client):
        """Test file tree when repo is too large."""
        mock_response = {
            "tree": [],
            "truncated": True
        }
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (mock_response, None)
            
            files, error = await client.get_repository_tree("owner", "repo", "main")
            
            assert files is None
            assert error is not None
            assert "too large" in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_get_readme_success(self, client):
        """Test successful README fetch."""
        readme_content = "# My Project\n\nThis is a test project."
        
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = readme_content
            mock_instance.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_instance
            
            content, error = await client.get_readme("owner", "repo")
            
            assert error is None
            assert content == readme_content
    
    @pytest.mark.asyncio
    async def test_get_readme_not_found(self, client):
        """Test README fetch when not present."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_instance.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_instance
            
            content, error = await client.get_readme("owner", "repo")
            
            # No README is not an error
            assert error is None
            assert content is None
    
    @pytest.mark.asyncio
    async def test_get_languages_success(self, client):
        """Test successful language detection."""
        mock_response = {
            "Python": 50000,
            "JavaScript": 30000,
            "HTML": 10000
        }
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = (mock_response, None)
            
            languages, error = await client.get_languages("owner", "repo")
            
            assert error is None
            assert languages is not None
            assert languages["Python"] == 50000


# ============================================================================
# Ingestion Service Tests
# ============================================================================

class TestIngestionService:
    """Tests for the complete ingestion pipeline."""
    
    @pytest.fixture
    def service(self):
        """Create an ingestion service instance."""
        return IngestionService()
    
    @pytest.mark.asyncio
    async def test_ingest_invalid_url(self, service):
        """Test ingestion with invalid URL."""
        result = await service.ingest("not-a-valid-url")
        
        assert isinstance(result, IngestionError)
        assert result.error_type == "INVALID_URL"
    
    @pytest.mark.asyncio
    async def test_ingest_user_profile_url(self, service):
        """Test ingestion with user profile URL."""
        result = await service.ingest("https://github.com/username")
        
        assert isinstance(result, IngestionError)
        assert result.error_type == "INVALID_URL"
    
    @pytest.mark.asyncio
    async def test_ingest_success(self, service):
        """Test successful ingestion."""
        mock_metadata = RepositoryMetadata(
            name="test-repo",
            owner="test-owner",
            default_branch="main",
            size=1234,
            primary_language="Python"
        )
        
        mock_files = [
            FileEntry(path="README.md", name="README.md", extension="md", type="file"),
            FileEntry(path="src", name="src", extension=None, type="directory"),
            FileEntry(path="src/main.py", name="main.py", extension="py", type="file"),
        ]
        
        mock_languages = {"Python": 50000, "Markdown": 5000}
        mock_readme = "# Test Project\n\nDescription here."
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock_exists, \
             patch.object(service.github_client, "get_repository_metadata", new_callable=AsyncMock) as mock_meta, \
             patch.object(service.github_client, "get_repository_tree", new_callable=AsyncMock) as mock_tree, \
             patch.object(service.github_client, "get_languages", new_callable=AsyncMock) as mock_langs, \
             patch.object(service.github_client, "get_readme", new_callable=AsyncMock) as mock_readme_fetch:
            
            mock_exists.return_value = (True, None)
            mock_meta.return_value = (mock_metadata, None)
            mock_tree.return_value = (mock_files, None)
            mock_langs.return_value = (mock_languages, None)
            mock_readme_fetch.return_value = (mock_readme, None)
            
            result = await service.ingest("https://github.com/test-owner/test-repo")
            
            assert isinstance(result, IngestedRepository)
            assert result.repo_name == "test-repo"
            assert result.owner == "test-owner"
            assert result.default_branch == "main"
            assert len(result.files) == 3
            assert result.languages["Python"] == 50000
            assert result.readme == mock_readme
    
    @pytest.mark.asyncio
    async def test_ingest_private_repo(self, service):
        """Test ingestion of private repository."""
        error = GitHubError(
            error_type="PRIVATE_REPO",
            message="Repository is not accessible",
            details="The repository may be private"
        )
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock:
            mock.return_value = (False, error)
            
            result = await service.ingest("https://github.com/owner/private-repo")
            
            assert isinstance(result, IngestionError)
            assert result.error_type == "PRIVATE_REPO"
    
    @pytest.mark.asyncio
    async def test_ingest_not_found(self, service):
        """Test ingestion of non-existent repository."""
        error = GitHubError(
            error_type="NOT_FOUND",
            message="Repository not found",
            details="404"
        )
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock:
            mock.return_value = (False, error)
            
            result = await service.ingest("https://github.com/owner/nonexistent")
            
            assert isinstance(result, IngestionError)
            assert result.error_type == "NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_ingest_empty_repo(self, service):
        """Test ingestion of empty repository (no files)."""
        mock_metadata = RepositoryMetadata(
            name="empty-repo",
            owner="owner",
            default_branch="main",
            size=0,
            primary_language=None
        )
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock_exists, \
             patch.object(service.github_client, "get_repository_metadata", new_callable=AsyncMock) as mock_meta, \
             patch.object(service.github_client, "get_repository_tree", new_callable=AsyncMock) as mock_tree, \
             patch.object(service.github_client, "get_languages", new_callable=AsyncMock) as mock_langs, \
             patch.object(service.github_client, "get_readme", new_callable=AsyncMock) as mock_readme:
            
            mock_exists.return_value = (True, None)
            mock_meta.return_value = (mock_metadata, None)
            mock_tree.return_value = ([], None)
            mock_langs.return_value = ({}, None)
            mock_readme.return_value = (None, None)
            
            result = await service.ingest("https://github.com/owner/empty-repo")
            
            assert isinstance(result, IngestedRepository)
            assert len(result.files) == 0
            assert result.readme is None
            assert result.languages == {}
    
    @pytest.mark.asyncio
    async def test_ingest_no_readme(self, service):
        """Test ingestion of repo without README."""
        mock_metadata = RepositoryMetadata(
            name="no-readme-repo",
            owner="owner",
            default_branch="main",
            size=100,
            primary_language="Python"
        )
        
        mock_files = [
            FileEntry(path="main.py", name="main.py", extension="py", type="file"),
        ]
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock_exists, \
             patch.object(service.github_client, "get_repository_metadata", new_callable=AsyncMock) as mock_meta, \
             patch.object(service.github_client, "get_repository_tree", new_callable=AsyncMock) as mock_tree, \
             patch.object(service.github_client, "get_languages", new_callable=AsyncMock) as mock_langs, \
             patch.object(service.github_client, "get_readme", new_callable=AsyncMock) as mock_readme:
            
            mock_exists.return_value = (True, None)
            mock_meta.return_value = (mock_metadata, None)
            mock_tree.return_value = (mock_files, None)
            mock_langs.return_value = ({"Python": 1000}, None)
            mock_readme.return_value = (None, None)  # No README
            
            result = await service.ingest("https://github.com/owner/no-readme-repo")
            
            assert isinstance(result, IngestedRepository)
            assert result.readme is None
    
    @pytest.mark.asyncio
    async def test_ingest_rate_limited(self, service):
        """Test ingestion when rate limited."""
        error = GitHubError(
            error_type="RATE_LIMITED",
            message="Rate limit exceeded",
            details="Try again later"
        )
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock:
            mock.return_value = (False, error)
            
            result = await service.ingest("https://github.com/owner/repo")
            
            assert isinstance(result, IngestionError)
            assert result.error_type == "RATE_LIMITED"
    
    @pytest.mark.asyncio
    async def test_deterministic_output(self, service):
        """Test that same input produces same output (determinism)."""
        mock_metadata = RepositoryMetadata(
            name="test-repo",
            owner="owner",
            default_branch="main",
            size=100,
            primary_language="Python"
        )
        
        mock_files = [
            FileEntry(path="main.py", name="main.py", extension="py", type="file"),
        ]
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock_exists, \
             patch.object(service.github_client, "get_repository_metadata", new_callable=AsyncMock) as mock_meta, \
             patch.object(service.github_client, "get_repository_tree", new_callable=AsyncMock) as mock_tree, \
             patch.object(service.github_client, "get_languages", new_callable=AsyncMock) as mock_langs, \
             patch.object(service.github_client, "get_readme", new_callable=AsyncMock) as mock_readme:
            
            mock_exists.return_value = (True, None)
            mock_meta.return_value = (mock_metadata, None)
            mock_tree.return_value = (mock_files, None)
            mock_langs.return_value = ({"Python": 1000}, None)
            mock_readme.return_value = ("# Test", None)
            
            # Run twice
            result1 = await service.ingest("https://github.com/owner/test-repo")
            result2 = await service.ingest("https://github.com/owner/test-repo")
            
            # Both should be identical
            assert isinstance(result1, IngestedRepository)
            assert isinstance(result2, IngestedRepository)
            assert result1.to_dict() == result2.to_dict()


# ============================================================================
# Output Schema Validation Tests
# ============================================================================

class TestOutputSchema:
    """Tests to verify output matches the required schema."""
    
    @pytest.mark.asyncio
    async def test_success_output_schema(self):
        """Test that success output matches the required schema."""
        service = IngestionService()
        
        mock_metadata = RepositoryMetadata(
            name="schema-test",
            owner="owner",
            default_branch="main",
            size=100,
            primary_language="Python"
        )
        
        mock_files = [
            FileEntry(path="README.md", name="README.md", extension="md", type="file"),
        ]
        
        with patch.object(service.github_client, "check_repository_exists", new_callable=AsyncMock) as mock_exists, \
             patch.object(service.github_client, "get_repository_metadata", new_callable=AsyncMock) as mock_meta, \
             patch.object(service.github_client, "get_repository_tree", new_callable=AsyncMock) as mock_tree, \
             patch.object(service.github_client, "get_languages", new_callable=AsyncMock) as mock_langs, \
             patch.object(service.github_client, "get_readme", new_callable=AsyncMock) as mock_readme:
            
            mock_exists.return_value = (True, None)
            mock_meta.return_value = (mock_metadata, None)
            mock_tree.return_value = (mock_files, None)
            mock_langs.return_value = ({"Python": 1000}, None)
            mock_readme.return_value = ("# Test", None)
            
            result = await service.ingest("https://github.com/owner/schema-test")
            
            assert isinstance(result, IngestedRepository)
            output = result.to_dict()
            
            # Verify schema
            assert "repo_name" in output
            assert "owner" in output
            assert "default_branch" in output
            assert "languages" in output
            assert "files" in output
            assert "readme" in output
            
            # Verify types
            assert isinstance(output["repo_name"], str)
            assert isinstance(output["owner"], str)
            assert isinstance(output["default_branch"], str)
            assert isinstance(output["languages"], dict)
            assert isinstance(output["files"], list)
            assert output["readme"] is None or isinstance(output["readme"], str)
            
            # Verify file entry schema
            for file in output["files"]:
                assert "path" in file
                assert "name" in file
                assert "extension" in file
                assert "type" in file
                assert file["type"] in ["file", "directory"]
    
    def test_error_output_schema(self):
        """Test that error output matches the required schema."""
        error = IngestionError(
            error_type="NOT_FOUND",
            message="Repository not found",
            details="The repository does not exist"
        )
        
        output = error.to_dict()
        
        # Verify schema
        assert "error" in output
        assert "type" in output["error"]
        assert "message" in output["error"]
        assert "details" in output["error"]
        
        # Verify types
        assert isinstance(output["error"]["type"], str)
        assert isinstance(output["error"]["message"], str)
        assert output["error"]["details"] is None or isinstance(output["error"]["details"], str)
        
        # Verify error type is valid
        valid_types = ["INVALID_URL", "PRIVATE_REPO", "NOT_FOUND", "RATE_LIMITED", "UNKNOWN"]
        assert output["error"]["type"] in valid_types
