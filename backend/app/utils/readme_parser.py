"""
README Section Parser

This module provides deterministic parsing of README content to detect
the presence of key sections. No AI, just pattern matching.

All functions are pure and deterministic:
- Same input → same output
- No external state
- No randomness
"""

import re
from dataclasses import dataclass


@dataclass
class ReadmeAnalysis:
    """
    Analysis result for README content.
    
    Contains presence flags for key sections and metrics.
    """
    exists: bool
    char_count: int
    has_installation: bool
    has_usage: bool
    has_features: bool
    has_license_section: bool
    
    @property
    def section_count(self) -> int:
        """Count of detected key sections (max 4)."""
        return sum([
            self.has_installation,
            self.has_usage,
            self.has_features,
            self.has_license_section
        ])


# Section detection patterns (case-insensitive)
# These patterns match common markdown heading formats
SECTION_PATTERNS: dict[str, list[str]] = {
    "installation": [
        r"#+\s*install",
        r"#+\s*getting\s+started",
        r"#+\s*setup",
        r"#+\s*quick\s*start",
        r"\*\*install",
        r"##\s*prerequisites",
    ],
    "usage": [
        r"#+\s*usage",
        r"#+\s*how\s+to\s+use",
        r"#+\s*examples?",
        r"#+\s*running",
        r"#+\s*run\s+the",
    ],
    "features": [
        r"#+\s*features?",
        r"#+\s*what\s+it\s+does",
        r"#+\s*capabilities",
        r"#+\s*highlights",
        r"#+\s*key\s+features",
    ],
    "license": [
        r"#+\s*license",
        r"#+\s*licensing",
        r"\*\*license",
    ],
}


def _has_section(content: str, patterns: list[str]) -> bool:
    """
    Check if content contains any of the given patterns.
    
    Args:
        content: The README content (lowercased)
        patterns: List of regex patterns to match
        
    Returns:
        True if any pattern matches, False otherwise
    """
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def analyze_readme(readme_content: str | None) -> ReadmeAnalysis:
    """
    Analyze README content for key sections and metrics.
    
    This function is fully deterministic:
    - Same input always produces the same output
    - No AI or probabilistic logic
    - Pure pattern matching
    
    Args:
        readme_content: The README content string, or None if missing
        
    Returns:
        ReadmeAnalysis with section detection results
    """
    if readme_content is None or readme_content.strip() == "":
        return ReadmeAnalysis(
            exists=False,
            char_count=0,
            has_installation=False,
            has_usage=False,
            has_features=False,
            has_license_section=False,
        )
    
    content = readme_content.strip()
    content_lower = content.lower()
    
    return ReadmeAnalysis(
        exists=True,
        char_count=len(content),
        has_installation=_has_section(content_lower, SECTION_PATTERNS["installation"]),
        has_usage=_has_section(content_lower, SECTION_PATTERNS["usage"]),
        has_features=_has_section(content_lower, SECTION_PATTERNS["features"]),
        has_license_section=_has_section(content_lower, SECTION_PATTERNS["license"]),
    )
