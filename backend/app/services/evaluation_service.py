"""
Rule-Based Evaluation Service

This module implements the Phase 2 deterministic evaluation engine.
It evaluates a repository using explicit, traceable rules with zero AI dependency.

Hard Constraints:
- No AI reasoning or inference
- No probabilistic logic
- No external data sources
- No network calls
- Same input must always produce the same output
- All rules must be explainable and traceable
- All scores must be derived from explicit conditions
"""

from dataclasses import dataclass, field
from typing import Any

from app.services.ingestion_service import IngestedRepository
from app.utils.readme_parser import analyze_readme, ReadmeAnalysis


@dataclass
class EvaluationResult:
    """
    Complete evaluation result from the rule-based engine.
    
    All scores are 0-10 scale.
    Issues are actionable, specific, and non-judgmental.
    """
    documentation_score: int
    structure_score: int
    configuration_score: int
    completeness_score: int
    issues: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching the output schema."""
        return {
            "documentation_score": self.documentation_score,
            "structure_score": self.structure_score,
            "configuration_score": self.configuration_score,
            "completeness_score": self.completeness_score,
            "issues": self.issues,
        }


# ============================================================================
# Configuration Constants
# ============================================================================

# Recognized source directory names
SOURCE_DIRECTORIES = frozenset({
    "src", "source", "lib", "app", "backend", "frontend",
    "core", "pkg", "packages", "modules", "components"
})

# Configuration files to detect
CONFIG_FILES = {
    "gitignore": {".gitignore"},
    "license": {"license", "license.md", "license.txt", "copying", "copying.md"},
    "dependency": {
        "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
        "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "go.mod", "cargo.toml", "gemfile", "build.gradle", "pom.xml",
        "composer.json", "mix.exs", "project.clj"
    },
    "readme": {"readme", "readme.md", "readme.txt", "readme.rst"}
}

# Maximum files at root before penalty
MAX_ROOT_FILES = 10


class EvaluationService:
    """
    Rule-Based Repository Evaluation Engine.
    
    Evaluates repositories using deterministic rules applied to
    structured data from Phase 1. Zero AI dependency.
    
    All evaluation methods are pure functions:
    - Same input → same output
    - No side effects
    - No external state
    """
    
    def evaluate(self, repository: IngestedRepository) -> EvaluationResult:
        """
        Execute the complete evaluation pipeline.
        
        Evaluates all dimensions independently then aggregates.
        
        Args:
            repository: The ingested repository data from Phase 1
            
        Returns:
            EvaluationResult with scores and issues
        """
        issues: list[str] = []
        
        # Run all evaluations
        doc_score, doc_issues = self._evaluate_documentation(repository.readme)
        structure_score, structure_issues = self._evaluate_structure(repository.files)
        config_score, config_issues = self._evaluate_configuration(repository.files)
        completeness_score, completeness_issues = self._evaluate_completeness(repository)
        
        # Aggregate issues
        issues.extend(doc_issues)
        issues.extend(structure_issues)
        issues.extend(config_issues)
        issues.extend(completeness_issues)
        
        return EvaluationResult(
            documentation_score=doc_score,
            structure_score=structure_score,
            configuration_score=config_score,
            completeness_score=completeness_score,
            issues=issues,
        )
    
    def _evaluate_documentation(self, readme: str | None) -> tuple[int, list[str]]:
        """
        Evaluate documentation using explicit, countable rules.
        
        Scoring Rules (0-10):
        - README missing → score = 0
        - README exists → base score = 3
        - README length ≥ 300 chars → +2
        - README length ≥ 800 chars → +2
        - Each key section present → +1 (max +3, capped to reach 10)
        
        Cap at 10.
        
        Args:
            readme: README content or None
            
        Returns:
            Tuple of (score, list of issues)
        """
        issues: list[str] = []
        analysis = analyze_readme(readme)
        
        # README missing → score = 0
        if not analysis.exists:
            issues.append("README is missing")
            return (0, issues)
        
        # Base score for README existing
        score = 3
        
        # Length bonuses
        if analysis.char_count >= 300:
            score += 2
        else:
            issues.append("README is too short (less than 300 characters)")
        
        if analysis.char_count >= 800:
            score += 2
        
        # Section bonuses (max +3 to cap at 10)
        section_bonus = 0
        max_section_bonus = 3
        
        if analysis.has_installation:
            section_bonus += 1
        else:
            issues.append("README is missing an Installation section")
            
        if analysis.has_usage:
            section_bonus += 1
        else:
            issues.append("README is missing a Usage section")
            
        if analysis.has_features:
            section_bonus += 1
        else:
            issues.append("README is missing a Features section")
        
        # License section check (informational, doesn't add to bonus beyond cap)
        if not analysis.has_license_section:
            issues.append("README is missing a License section")
        else:
            section_bonus += 1
        
        # Apply capped section bonus
        score += min(section_bonus, max_section_bonus)
        
        # Cap at 10
        return (min(score, 10), issues)
    
    def _evaluate_structure(self, files: list[dict[str, Any]]) -> tuple[int, list[str]]:
        """
        Evaluate repository structure consistency.
        
        Scoring Rules (0-10):
        - Base score = 5
        - No source directory → -3
        - Root files ≤ 10 → +3
        - Recognizable structure (src, app, backend, frontend) → +4
        - Deep nesting without structure → -2
        
        Minimum score = 0.
        
        Args:
            files: List of file entries from repository
            
        Returns:
            Tuple of (score, list of issues)
        """
        issues: list[str] = []
        score = 5  # Base score
        
        # Extract file paths and analyze structure
        root_files = []
        root_directories = set()
        has_source_dir = False
        has_deep_nesting = False
        max_depth = 0
        
        for file_entry in files:
            path = file_entry.get("path", "")
            file_type = file_entry.get("type", "file")
            
            # Count path depth
            parts = path.strip("/").split("/")
            depth = len(parts)
            max_depth = max(max_depth, depth)
            
            # Check for deep nesting (more than 5 levels)
            if depth > 5:
                has_deep_nesting = True
            
            # Analyze root level
            if len(parts) == 1:
                if file_type == "directory":
                    root_directories.add(parts[0].lower())
                else:
                    root_files.append(parts[0])
            elif len(parts) >= 1:
                # Top-level directory
                root_directories.add(parts[0].lower())
        
        # Check for recognizable source directories
        recognized_dirs = root_directories.intersection(SOURCE_DIRECTORIES)
        has_source_dir = len(recognized_dirs) > 0
        
        # Apply scoring rules
        if not has_source_dir:
            score -= 3
            issues.append("No recognizable source directory found (e.g., src/, app/, backend/)")
        else:
            score += 4  # Recognizable structure bonus
        
        # Root file count check (only count files, not directories)
        root_file_count = len(root_files)
        if root_file_count <= MAX_ROOT_FILES:
            score += 3
        else:
            issues.append(f"Too many files in repository root ({root_file_count} files, recommended ≤ {MAX_ROOT_FILES})")
        
        # Deep nesting penalty
        if has_deep_nesting and not has_source_dir:
            score -= 2
            issues.append("Deep file nesting detected without clear directory structure")
        
        # Ensure score is within valid range [0, 10]
        return (max(0, min(score, 10)), issues)
    
    def _evaluate_configuration(self, files: list[dict[str, Any]]) -> tuple[int, list[str]]:
        """
        Check for common configuration and metadata files.
        
        Files to Detect:
        - .gitignore
        - LICENSE
        - requirements.txt, pyproject.toml, package.json, etc.
        - README
        
        Scoring Rules (0-10):
        - .gitignore present → +3
        - License present → +3
        - Dependency file present → +4
        
        Args:
            files: List of file entries from repository
            
        Returns:
            Tuple of (score, list of issues)
        """
        issues: list[str] = []
        score = 0
        
        # Build set of lowercase file names for matching
        file_names = set()
        for file_entry in files:
            name = file_entry.get("name", "").lower()
            file_names.add(name)
        
        # Check for .gitignore
        has_gitignore = bool(file_names.intersection(CONFIG_FILES["gitignore"]))
        if has_gitignore:
            score += 3
        else:
            issues.append("No .gitignore file found")
        
        # Check for license
        has_license = bool(file_names.intersection(CONFIG_FILES["license"]))
        if has_license:
            score += 3
        else:
            issues.append("No LICENSE file found")
        
        # Check for dependency file
        has_dependency = bool(file_names.intersection(CONFIG_FILES["dependency"]))
        if has_dependency:
            score += 4
        else:
            issues.append("No dependency file found (e.g., requirements.txt, package.json)")
        
        return (score, issues)
    
    def _evaluate_completeness(self, repository: IngestedRepository) -> tuple[int, list[str]]:
        """
        Evaluate signals that indicate a "finished" project.
        
        Signals:
        - README exists
        - License exists
        - Dependency file exists
        - Multiple directories present
        
        Scoring Rules (0-10):
        - Each signal present → +2.5 (rounded to int)
        
        Args:
            repository: The ingested repository data
            
        Returns:
            Tuple of (score, list of issues)
        """
        issues: list[str] = []
        signals_present = 0
        
        # Build file name set
        file_names = set()
        directory_count = 0
        
        for file_entry in repository.files:
            name = file_entry.get("name", "").lower()
            file_names.add(name)
            if file_entry.get("type") == "directory":
                directory_count += 1
        
        # Signal 1: README exists
        has_readme = repository.readme is not None and repository.readme.strip() != ""
        if has_readme:
            signals_present += 1
        else:
            issues.append("Project appears incomplete: README is missing")
        
        # Signal 2: License exists
        has_license = bool(file_names.intersection(CONFIG_FILES["license"]))
        if has_license:
            signals_present += 1
        else:
            issues.append("Project appears incomplete: LICENSE is missing")
        
        # Signal 3: Dependency file exists
        has_dependency = bool(file_names.intersection(CONFIG_FILES["dependency"]))
        if has_dependency:
            signals_present += 1
        else:
            issues.append("Project appears incomplete: no dependency management file")
        
        # Signal 4: Multiple directories present (indicates organized structure)
        has_multiple_dirs = directory_count >= 2
        if has_multiple_dirs:
            signals_present += 1
        else:
            issues.append("Project appears incomplete: lacks directory organization")
        
        # Calculate score: 2.5 per signal, rounded
        score = round(signals_present * 2.5)
        
        return (score, issues)


# ============================================================================
# Service Factory
# ============================================================================

_evaluation_service: EvaluationService | None = None


def get_evaluation_service() -> EvaluationService:
    """
    Get or create the evaluation service instance.
    
    Returns:
        The singleton EvaluationService instance
    """
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = EvaluationService()
    return _evaluation_service
