"""
Prompts Module

Contains LLM prompt templates and prompt management logic
for AI-powered analysis components.

Prompt Files:
- documentation_quality.prompt: README clarity analysis
- code_clarity.prompt: Structure-based code clarity signals
- tech_stack_analysis.prompt: Tech stack usage explanation
- recruiter_feedback.prompt: Recruiter-style feedback

All prompts are versioned and follow strict output schemas.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

PROMPT_FILES = {
    "documentation_quality": PROMPTS_DIR / "documentation_quality.prompt",
    "code_clarity": PROMPTS_DIR / "code_clarity.prompt",
    "tech_stack_analysis": PROMPTS_DIR / "tech_stack_analysis.prompt",
    "recruiter_feedback": PROMPTS_DIR / "recruiter_feedback.prompt",
}


def get_prompt(name: str) -> str:
    """Load a prompt template by name."""
    if name not in PROMPT_FILES:
        raise ValueError(f"Unknown prompt: {name}. Available: {list(PROMPT_FILES.keys())}")
    return PROMPT_FILES[name].read_text(encoding="utf-8")


def list_prompts() -> list[str]:
    """List available prompt names."""
    return list(PROMPT_FILES.keys())
