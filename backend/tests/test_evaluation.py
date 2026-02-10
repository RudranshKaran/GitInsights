"""
Unit Tests for Rule-Based Evaluation (Phase 2)

Tests cover all scenarios specified in Phase 2 requirements:
- Determinism: Same input → same output
- Documentation evaluation scoring
- Structure evaluation scoring
- Configuration evaluation scoring
- Completeness evaluation scoring
- Issue generation for all deduction paths

Hard Constraints Verified:
- No AI reasoning or inference
- No probabilistic logic
- All scores derived from explicit conditions
- All rules explainable and traceable
"""

import pytest
from app.utils.readme_parser import analyze_readme, ReadmeAnalysis
from app.services.evaluation_service import (
    EvaluationService,
    EvaluationResult,
    get_evaluation_service,
)
from app.services.ingestion_service import IngestedRepository


# ============================================================================
# README Parser Tests
# ============================================================================

class TestReadmeParser:
    """Tests for README section detection (deterministic pattern matching)."""
    
    def test_no_readme(self):
        """Test analysis when README is None."""
        result = analyze_readme(None)
        assert result.exists is False
        assert result.char_count == 0
        assert result.section_count == 0
    
    def test_empty_readme(self):
        """Test analysis when README is empty string."""
        result = analyze_readme("")
        assert result.exists is False
        assert result.char_count == 0
    
    def test_whitespace_only_readme(self):
        """Test analysis when README is only whitespace."""
        result = analyze_readme("   \n\t  ")
        assert result.exists is False
        assert result.char_count == 0
    
    def test_basic_readme_exists(self):
        """Test that a basic README is detected as existing."""
        result = analyze_readme("# My Project\n\nThis is my project.")
        assert result.exists is True
        assert result.char_count > 0
    
    def test_installation_section_detection(self):
        """Test detection of installation section."""
        readme = "# Project\n\n## Installation\n\nRun pip install"
        result = analyze_readme(readme)
        assert result.has_installation is True
    
    def test_installation_section_variations(self):
        """Test detection of various installation section formats."""
        variations = [
            "## Install",
            "### Getting Started",
            "# Setup",
            "## Quick Start",
            "## Prerequisites",
        ]
        for header in variations:
            result = analyze_readme(f"# Project\n\n{header}\n\nContent here")
            assert result.has_installation is True, f"Failed to detect: {header}"
    
    def test_usage_section_detection(self):
        """Test detection of usage section."""
        readme = "# Project\n\n## Usage\n\nHow to use this"
        result = analyze_readme(readme)
        assert result.has_usage is True
    
    def test_usage_section_variations(self):
        """Test detection of various usage section formats."""
        variations = [
            "## How to Use",
            "## Examples",
            "# Running",
            "## Run the app",
        ]
        for header in variations:
            result = analyze_readme(f"# Project\n\n{header}\n\nContent here")
            assert result.has_usage is True, f"Failed to detect: {header}"
    
    def test_features_section_detection(self):
        """Test detection of features section."""
        readme = "# Project\n\n## Features\n\n- Feature 1\n- Feature 2"
        result = analyze_readme(readme)
        assert result.has_features is True
    
    def test_features_section_variations(self):
        """Test detection of various features section formats."""
        variations = [
            "## Feature",
            "# Key Features",
            "## Highlights",
            "## What it Does",
        ]
        for header in variations:
            result = analyze_readme(f"# Project\n\n{header}\n\nContent here")
            assert result.has_features is True, f"Failed to detect: {header}"
    
    def test_license_section_detection(self):
        """Test detection of license section."""
        readme = "# Project\n\n## License\n\nMIT License"
        result = analyze_readme(readme)
        assert result.has_license_section is True
    
    def test_section_count(self):
        """Test that section_count property works correctly."""
        readme = """
# Project

## Installation
Run pip install

## Usage
Use it like this

## Features
- Feature 1

## License
MIT
"""
        result = analyze_readme(readme)
        assert result.section_count == 4
    
    def test_no_sections_detected(self):
        """Test README with no recognized sections."""
        readme = "# My Project\n\nJust some text here with no sections."
        result = analyze_readme(readme)
        assert result.has_installation is False
        assert result.has_usage is False
        assert result.has_features is False
        assert result.has_license_section is False
        assert result.section_count == 0
    
    def test_determinism(self):
        """Test that same input always produces same output."""
        readme = "# Test\n\n## Installation\n\n## Usage"
        result1 = analyze_readme(readme)
        result2 = analyze_readme(readme)
        
        assert result1.exists == result2.exists
        assert result1.char_count == result2.char_count
        assert result1.has_installation == result2.has_installation
        assert result1.has_usage == result2.has_usage
        assert result1.has_features == result2.has_features
        assert result1.has_license_section == result2.has_license_section


# ============================================================================
# Evaluation Service Tests
# ============================================================================

class TestEvaluationService:
    """Tests for the Rule-Based Evaluation Service."""
    
    @pytest.fixture
    def service(self) -> EvaluationService:
        """Create evaluation service instance."""
        return EvaluationService()
    
    @pytest.fixture
    def minimal_repo(self) -> IngestedRepository:
        """Create a minimal repository fixture."""
        return IngestedRepository(
            repo_name="test-repo",
            owner="test-owner",
            default_branch="main",
            languages={"Python": 1000},
            files=[],
            readme=None,
        )
    
    @pytest.fixture
    def well_structured_repo(self) -> IngestedRepository:
        """Create a well-structured repository fixture."""
        return IngestedRepository(
            repo_name="good-repo",
            owner="good-owner",
            default_branch="main",
            languages={"Python": 5000, "JavaScript": 2000},
            files=[
                {"path": "src", "name": "src", "extension": None, "type": "directory"},
                {"path": "tests", "name": "tests", "extension": None, "type": "directory"},
                {"path": "docs", "name": "docs", "extension": None, "type": "directory"},
                {"path": "README.md", "name": "README.md", "extension": "md", "type": "file"},
                {"path": "LICENSE", "name": "LICENSE", "extension": None, "type": "file"},
                {"path": ".gitignore", "name": ".gitignore", "extension": None, "type": "file"},
                {"path": "requirements.txt", "name": "requirements.txt", "extension": "txt", "type": "file"},
                {"path": "src/main.py", "name": "main.py", "extension": "py", "type": "file"},
                {"path": "src/utils.py", "name": "utils.py", "extension": "py", "type": "file"},
            ],
            readme="""# Good Repo

A well-documented project with all sections. This repository demonstrates
best practices for project documentation and organization.

## Installation

Run `pip install -r requirements.txt` to install all dependencies.

Make sure you have Python 3.8 or higher installed on your system.

## Usage

```python
from good_repo import main
main.run()
```

You can also run directly from the command line:
```bash
python -m good_repo
```

## Features

- Feature 1: Does something amazing with great performance
- Feature 2: Does something else that users love
- Feature 3: More functionality for power users
- Feature 4: Integration with popular tools

## License

MIT License - see LICENSE file for full details.

This is a comprehensive README with over 800 characters to ensure
we get the full length bonus. Adding more text here to pad it out
and make sure we hit all the thresholds for maximum documentation score.
The project follows best practices and is well-maintained.
""",
        )


class TestDocumentationEvaluation(TestEvaluationService):
    """Tests for documentation scoring rules."""
    
    def test_missing_readme_scores_zero(self, service, minimal_repo):
        """README missing → score = 0."""
        result = service.evaluate(minimal_repo)
        assert result.documentation_score == 0
        assert "README is missing" in result.issues
    
    def test_readme_exists_base_score(self, service, minimal_repo):
        """README exists → base score = 3."""
        minimal_repo.readme = "# Test"
        result = service.evaluate(minimal_repo)
        assert result.documentation_score >= 3
    
    def test_readme_length_300_bonus(self, service, minimal_repo):
        """README length ≥ 300 chars → +2."""
        minimal_repo.readme = "# Test\n" + "x" * 300
        result = service.evaluate(minimal_repo)
        # Base 3 + length bonus 2 = 5
        assert result.documentation_score >= 5
    
    def test_readme_length_800_bonus(self, service, minimal_repo):
        """README length ≥ 800 chars → +2 additional."""
        minimal_repo.readme = "# Test\n" + "x" * 800
        result = service.evaluate(minimal_repo)
        # Base 3 + length 300 bonus 2 + length 800 bonus 2 = 7
        assert result.documentation_score >= 7
    
    def test_readme_short_generates_issue(self, service, minimal_repo):
        """Short README should generate issue."""
        minimal_repo.readme = "# Short"
        result = service.evaluate(minimal_repo)
        assert any("short" in issue.lower() or "300" in issue for issue in result.issues)
    
    def test_readme_section_bonuses(self, service, minimal_repo):
        """Each key section present → +1 (max +3)."""
        minimal_repo.readme = """# Test

## Installation
Install it

## Usage
Use it

## Features
- Feature 1
"""
        result = service.evaluate(minimal_repo)
        # Base 3 + some section bonuses
        assert result.documentation_score >= 3
    
    def test_missing_sections_generate_issues(self, service, minimal_repo):
        """Missing sections should generate issues."""
        minimal_repo.readme = "# Just a title"
        result = service.evaluate(minimal_repo)
        
        section_issues = [i for i in result.issues if "section" in i.lower()]
        assert len(section_issues) >= 1
    
    def test_max_documentation_score_capped_at_10(self, service, well_structured_repo):
        """Documentation score should be capped at 10."""
        result = service.evaluate(well_structured_repo)
        assert result.documentation_score <= 10
    
    def test_perfect_documentation_scores_10(self, service, well_structured_repo):
        """Well-documented repo should score 10."""
        result = service.evaluate(well_structured_repo)
        assert result.documentation_score == 10


class TestStructureEvaluation(TestEvaluationService):
    """Tests for structure scoring rules."""
    
    def test_no_source_directory_penalty(self, service, minimal_repo):
        """No source directory → -3 from base."""
        minimal_repo.files = [
            {"path": "file1.py", "name": "file1.py", "extension": "py", "type": "file"},
            {"path": "file2.py", "name": "file2.py", "extension": "py", "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        # Base 5 - 3 (no src) + 3 (few root files) = 5
        assert "No recognizable source directory" in " ".join(result.issues)
    
    def test_recognizable_source_directory_bonus(self, service, minimal_repo):
        """Recognizable structure → +4."""
        minimal_repo.files = [
            {"path": "src", "name": "src", "extension": None, "type": "directory"},
            {"path": "src/main.py", "name": "main.py", "extension": "py", "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        # Base 5 + 4 (src dir) + 3 (few files) = 12, but let's verify it's high
        assert result.structure_score >= 8
    
    def test_various_source_directories_recognized(self, service, minimal_repo):
        """Test that various source directory names are recognized."""
        source_dirs = ["src", "app", "backend", "frontend", "lib", "core"]
        
        for dir_name in source_dirs:
            minimal_repo.files = [
                {"path": dir_name, "name": dir_name, "extension": None, "type": "directory"},
            ]
            result = service.evaluate(minimal_repo)
            has_src_issue = any("source directory" in i.lower() for i in result.issues)
            assert not has_src_issue, f"Failed to recognize: {dir_name}"
    
    def test_too_many_root_files_penalty(self, service, minimal_repo):
        """Too many files at root → penalty and issue."""
        minimal_repo.files = [
            {"path": f"file{i}.py", "name": f"file{i}.py", "extension": "py", "type": "file"}
            for i in range(15)
        ]
        result = service.evaluate(minimal_repo)
        assert any("root" in issue.lower() for issue in result.issues)
    
    def test_few_root_files_bonus(self, service, minimal_repo):
        """Root files ≤ 10 → +3."""
        minimal_repo.files = [
            {"path": "src", "name": "src", "extension": None, "type": "directory"},
            {"path": "README.md", "name": "README.md", "extension": "md", "type": "file"},
            {"path": "LICENSE", "name": "LICENSE", "extension": None, "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        # Should get the root files bonus
        assert result.structure_score >= 5
    
    def test_structure_score_minimum_zero(self, service, minimal_repo):
        """Structure score should never go below 0."""
        # Worst case: no src dir, many root files, deep nesting
        minimal_repo.files = [
            {"path": f"file{i}.txt", "name": f"file{i}.txt", "extension": "txt", "type": "file"}
            for i in range(20)
        ]
        result = service.evaluate(minimal_repo)
        assert result.structure_score >= 0


class TestConfigurationEvaluation(TestEvaluationService):
    """Tests for configuration scoring rules."""
    
    def test_gitignore_bonus(self, service, minimal_repo):
        """.gitignore present → +3."""
        minimal_repo.files = [
            {"path": ".gitignore", "name": ".gitignore", "extension": None, "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        assert result.configuration_score >= 3
    
    def test_license_bonus(self, service, minimal_repo):
        """License present → +3."""
        minimal_repo.files = [
            {"path": "LICENSE", "name": "LICENSE", "extension": None, "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        assert result.configuration_score >= 3
    
    def test_license_variations(self, service, minimal_repo):
        """Test that various license file names are recognized."""
        license_names = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
        
        for name in license_names:
            minimal_repo.files = [
                {"path": name, "name": name, "extension": None, "type": "file"},
            ]
            result = service.evaluate(minimal_repo)
            assert result.configuration_score >= 3, f"Failed to recognize: {name}"
    
    def test_dependency_file_bonus(self, service, minimal_repo):
        """Dependency file present → +4."""
        minimal_repo.files = [
            {"path": "requirements.txt", "name": "requirements.txt", "extension": "txt", "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        assert result.configuration_score >= 4
    
    def test_various_dependency_files(self, service, minimal_repo):
        """Test that various dependency files are recognized."""
        dep_files = ["requirements.txt", "package.json", "pyproject.toml", "go.mod", "Cargo.toml"]
        
        for name in dep_files:
            minimal_repo.files = [
                {"path": name, "name": name, "extension": None, "type": "file"},
            ]
            result = service.evaluate(minimal_repo)
            assert result.configuration_score >= 4, f"Failed to recognize: {name}"
    
    def test_full_configuration_score(self, service, minimal_repo):
        """All config files present → score = 10."""
        minimal_repo.files = [
            {"path": ".gitignore", "name": ".gitignore", "extension": None, "type": "file"},
            {"path": "LICENSE", "name": "LICENSE", "extension": None, "type": "file"},
            {"path": "requirements.txt", "name": "requirements.txt", "extension": "txt", "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        assert result.configuration_score == 10
    
    def test_missing_configs_generate_issues(self, service, minimal_repo):
        """Missing config files should generate issues."""
        minimal_repo.files = []
        result = service.evaluate(minimal_repo)
        
        assert any(".gitignore" in issue for issue in result.issues)
        assert any("LICENSE" in issue for issue in result.issues)
        assert any("dependency" in issue.lower() for issue in result.issues)


class TestCompletenessEvaluation(TestEvaluationService):
    """Tests for completeness scoring rules."""
    
    def test_readme_signal(self, service, minimal_repo):
        """README exists → +2.5 (rounded)."""
        minimal_repo.readme = "# Test"
        result_with = service.evaluate(minimal_repo)
        
        minimal_repo.readme = None
        result_without = service.evaluate(minimal_repo)
        
        assert result_with.completeness_score > result_without.completeness_score
    
    def test_license_signal(self, service, minimal_repo):
        """License exists → +2.5 (rounded)."""
        minimal_repo.files = [
            {"path": "LICENSE", "name": "LICENSE", "extension": None, "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        assert result.completeness_score >= 2  # At least one signal
    
    def test_dependency_signal(self, service, minimal_repo):
        """Dependency file exists → +2.5 (rounded)."""
        minimal_repo.files = [
            {"path": "requirements.txt", "name": "requirements.txt", "extension": "txt", "type": "file"},
        ]
        result = service.evaluate(minimal_repo)
        assert result.completeness_score >= 2  # At least one signal
    
    def test_multiple_directories_signal(self, service, minimal_repo):
        """Multiple directories present → +2.5 (rounded)."""
        minimal_repo.files = [
            {"path": "src", "name": "src", "extension": None, "type": "directory"},
            {"path": "tests", "name": "tests", "extension": None, "type": "directory"},
        ]
        result = service.evaluate(minimal_repo)
        assert result.completeness_score >= 2  # At least one signal
    
    def test_full_completeness_score(self, service, well_structured_repo):
        """All signals present → score = 10."""
        result = service.evaluate(well_structured_repo)
        assert result.completeness_score == 10
    
    def test_no_signals_score_zero(self, service, minimal_repo):
        """No signals → score = 0."""
        result = service.evaluate(minimal_repo)
        assert result.completeness_score == 0
    
    def test_incomplete_project_issues(self, service, minimal_repo):
        """Incomplete project should generate issues."""
        result = service.evaluate(minimal_repo)
        
        incomplete_issues = [i for i in result.issues if "incomplete" in i.lower()]
        assert len(incomplete_issues) >= 1


class TestDeterminism(TestEvaluationService):
    """Tests to verify deterministic behavior."""
    
    def test_same_input_same_output(self, service, well_structured_repo):
        """Same input must always produce the same output."""
        results = [service.evaluate(well_structured_repo) for _ in range(5)]
        
        first_result = results[0]
        for result in results[1:]:
            assert result.documentation_score == first_result.documentation_score
            assert result.structure_score == first_result.structure_score
            assert result.configuration_score == first_result.configuration_score
            assert result.completeness_score == first_result.completeness_score
            assert result.issues == first_result.issues
    
    def test_order_independence(self, service, minimal_repo):
        """File order should not affect results."""
        files = [
            {"path": "src", "name": "src", "extension": None, "type": "directory"},
            {"path": "LICENSE", "name": "LICENSE", "extension": None, "type": "file"},
            {"path": ".gitignore", "name": ".gitignore", "extension": None, "type": "file"},
        ]
        
        # Forward order
        minimal_repo.files = files.copy()
        result1 = service.evaluate(minimal_repo)
        
        # Reverse order
        minimal_repo.files = list(reversed(files))
        result2 = service.evaluate(minimal_repo)
        
        assert result1.documentation_score == result2.documentation_score
        assert result1.structure_score == result2.structure_score
        assert result1.configuration_score == result2.configuration_score
        assert result1.completeness_score == result2.completeness_score
    
    def test_to_dict_format(self, service, well_structured_repo):
        """Test that to_dict returns expected format."""
        result = service.evaluate(well_structured_repo)
        output = result.to_dict()
        
        assert "documentation_score" in output
        assert "structure_score" in output
        assert "configuration_score" in output
        assert "completeness_score" in output
        assert "issues" in output
        assert isinstance(output["issues"], list)


class TestServiceFactory:
    """Tests for the service factory function."""
    
    def test_get_evaluation_service_returns_instance(self):
        """get_evaluation_service should return an EvaluationService."""
        service = get_evaluation_service()
        assert isinstance(service, EvaluationService)
    
    def test_get_evaluation_service_singleton(self):
        """get_evaluation_service should return the same instance."""
        service1 = get_evaluation_service()
        service2 = get_evaluation_service()
        assert service1 is service2


class TestIssueGeneration:
    """Tests for issue generation rules."""
    
    @pytest.fixture
    def service(self) -> EvaluationService:
        return EvaluationService()
    
    @pytest.fixture
    def empty_repo(self) -> IngestedRepository:
        return IngestedRepository(
            repo_name="empty",
            owner="owner",
            default_branch="main",
            languages={},
            files=[],
            readme=None,
        )
    
    def test_issues_are_actionable(self, service, empty_repo):
        """Issues should be actionable (suggest what to do)."""
        result = service.evaluate(empty_repo)
        
        # All issues should be strings
        for issue in result.issues:
            assert isinstance(issue, str)
            assert len(issue) > 0
    
    def test_issues_are_specific(self, service, empty_repo):
        """Issues should be specific (mention what's missing)."""
        result = service.evaluate(empty_repo)
        
        # Should mention specific files/sections
        issue_text = " ".join(result.issues).lower()
        assert "readme" in issue_text or "license" in issue_text or "directory" in issue_text
    
    def test_issues_are_non_judgmental(self, service, empty_repo):
        """Issues should be non-judgmental (no blame or criticism)."""
        result = service.evaluate(empty_repo)
        
        judgmental_words = ["bad", "terrible", "awful", "wrong", "stupid", "poor"]
        issue_text = " ".join(result.issues).lower()
        
        for word in judgmental_words:
            assert word not in issue_text
    
    def test_each_deduction_generates_issue(self, service, empty_repo):
        """Every score deduction should generate an issue."""
        result = service.evaluate(empty_repo)
        
        # With an empty repo, we should have multiple issues
        assert len(result.issues) >= 4  # At least: README, LICENSE, gitignore, dependency


class TestScoreBoundaries:
    """Tests for score boundary conditions."""
    
    @pytest.fixture
    def service(self) -> EvaluationService:
        return EvaluationService()
    
    def test_all_scores_between_0_and_10(self, service):
        """All scores should be between 0 and 10."""
        test_cases = [
            IngestedRepository("test", "owner", "main", {}, [], None),
            IngestedRepository("test", "owner", "main", {"Python": 1000}, 
                             [{"path": "x", "name": "x", "extension": None, "type": "file"}] * 50,
                             "x" * 1000),
        ]
        
        for repo in test_cases:
            result = service.evaluate(repo)
            assert 0 <= result.documentation_score <= 10
            assert 0 <= result.structure_score <= 10
            assert 0 <= result.configuration_score <= 10
            assert 0 <= result.completeness_score <= 10
    
    def test_scores_are_integers(self, service):
        """All scores should be integers."""
        repo = IngestedRepository(
            "test", "owner", "main",
            {"Python": 1000},
            [{"path": "src", "name": "src", "extension": None, "type": "directory"}],
            "# Test\n" + "x" * 500
        )
        result = service.evaluate(repo)
        
        assert isinstance(result.documentation_score, int)
        assert isinstance(result.structure_score, int)
        assert isinstance(result.configuration_score, int)
        assert isinstance(result.completeness_score, int)
