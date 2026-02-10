"""
Report Generation Service (Phase 5)

Converts structured evaluation data (from Phases 1-4) into clear,
concise, human-readable outputs suitable for recruiters, interviewers,
and resume usage.

Key Constraints:
- Do NOT change or recompute scores
- Do NOT invent strengths or weaknesses
- Do NOT hallucinate missing information
- Do NOT use flowery or exaggerated language
- Output must strictly follow the schema
- Tone must be professional, neutral, and recruiter-friendly
- Same input must always produce the same output
"""

from dataclasses import dataclass
from typing import Literal

from app.schemas.models import (
    ReportGenerationInput,
    ReportGenerationOutput,
    ReportGenerationError,
    ReportGenerationErrorDetail,
    AIInsightsPayload,
    RuleEngineOutput,
    RepoMetadata,
    FinalScores,
)


# ============================================================================
# Score Interpretation Tables (Deterministic)
# ============================================================================

# Score ranges to descriptive terms
SCORE_INTERPRETATION: dict[str, str] = {
    "excellent": "demonstrates strong",
    "good": "shows solid",
    "adequate": "has acceptable",
    "needs_work": "requires improvement in",
}


def _interpret_score(score: float) -> str:
    """Map numeric score to interpretation key."""
    if score >= 8.0:
        return "excellent"
    elif score >= 6.0:
        return "good"
    elif score >= 4.0:
        return "adequate"
    else:
        return "needs_work"


# Clarity level to summary phrase
CLARITY_PHRASES: dict[str, str] = {
    "high": "Documentation is clear and comprehensive",
    "medium": "Documentation provides adequate coverage",
    "low": "Documentation needs significant improvement",
}

# Organization level to summary phrase
ORGANIZATION_PHRASES: dict[str, str] = {
    "well-structured": "with a well-organized project structure",
    "acceptable": "with an acceptable project structure",
    "poor": "though project structure could be improved",
}


class ReportGenerationService:
    """
    Report Generation Engine for Phase 5.
    
    Converts structured evaluation data into human-readable outputs.
    
    Responsibilities:
    1. Generate executive summary (3-5 sentences)
    2. Extract strengths from rule engine and AI insights
    3. Extract improvements from issues and AI gaps
    4. Generate resume-ready bullet points
    
    Guarantees:
    - Deterministic: Same input always produces same output
    - No hallucination: All output derived from input
    - Professional tone: Neutral, recruiter-friendly language
    - Bounded: Respects max item limits
    """
    
    def generate_report(
        self,
        input_data: ReportGenerationInput,
    ) -> ReportGenerationOutput | ReportGenerationError:
        """
        Generate the complete report from consolidated input.
        
        Args:
            input_data: ReportGenerationInput containing all Phase 1-4 data
            
        Returns:
            ReportGenerationOutput on success, ReportGenerationError on failure
        """
        # Validate input
        validation_error = self._validate_input(input_data)
        if validation_error:
            return validation_error
        
        # Generate all outputs
        summary = self._generate_executive_summary(
            repo_metadata=input_data.repo_metadata,
            rule_output=input_data.rule_engine_output,
            ai_insights=input_data.ai_insights,
            final_scores=input_data.final_scores,
        )
        
        strengths = self._extract_strengths(
            rule_output=input_data.rule_engine_output,
            ai_insights=input_data.ai_insights,
        )
        
        improvements = self._extract_improvements(
            rule_output=input_data.rule_engine_output,
            ai_insights=input_data.ai_insights,
        )
        
        resume_bullets = self._generate_resume_bullets(
            repo_metadata=input_data.repo_metadata,
            rule_output=input_data.rule_engine_output,
            ai_insights=input_data.ai_insights,
            strengths=strengths,
        )
        
        return ReportGenerationOutput(
            summary=summary,
            strengths=strengths,
            improvements=improvements,
            resume_bullets=resume_bullets,
        )
    
    def _validate_input(
        self,
        input_data: ReportGenerationInput,
    ) -> ReportGenerationError | None:
        """
        Validate input data structure.
        
        Returns error if required fields are missing or invalid.
        """
        if not input_data.repo_metadata.repo_name:
            return ReportGenerationError(
                error=ReportGenerationErrorDetail(
                    type="MISSING_INPUT",
                    message="Repository name is required",
                )
            )
        
        if input_data.rule_engine_output is None:
            return ReportGenerationError(
                error=ReportGenerationErrorDetail(
                    type="MISSING_INPUT",
                    message="Rule engine output is required",
                )
            )
        
        return None
    
    def _generate_executive_summary(
        self,
        repo_metadata: RepoMetadata,
        rule_output: RuleEngineOutput,
        ai_insights: AIInsightsPayload,
        final_scores: FinalScores,
    ) -> str:
        """
        Generate 3-5 sentence executive summary.
        
        Rules:
        - Neutral, recruiter-style tone
        - Mention overall readiness and clarity
        - No numeric scores inside text
        """
        sentences: list[str] = []
        repo_name = repo_metadata.repo_name
        
        # Sentence 1: Overall assessment based on final score
        score_level = _interpret_score(final_scores.final_score)
        if score_level == "excellent":
            sentences.append(
                f"{repo_name} is a well-prepared project that demonstrates strong technical foundations."
            )
        elif score_level == "good":
            sentences.append(
                f"{repo_name} shows solid project fundamentals with room for minor improvements."
            )
        elif score_level == "adequate":
            sentences.append(
                f"{repo_name} meets basic project standards but has notable areas needing attention."
            )
        else:
            sentences.append(
                f"{repo_name} requires significant improvements to meet professional project standards."
            )
        
        # Sentence 2: Documentation quality from AI insights or rule score
        if ai_insights.documentation_quality:
            clarity = ai_insights.documentation_quality.clarity
            doc_phrase = CLARITY_PHRASES.get(clarity, "Documentation provides basic information")
            sentences.append(f"{doc_phrase}.")
        elif rule_output.documentation_score >= 7:
            sentences.append("Documentation is comprehensive and well-structured.")
        elif rule_output.documentation_score >= 4:
            sentences.append("Documentation covers essential aspects but could be expanded.")
        else:
            sentences.append("Documentation requires substantial improvement.")
        
        # Sentence 3: Project structure from AI insights or rule score
        if ai_insights.code_clarity:
            org = ai_insights.code_clarity.organization
            org_phrase = ORGANIZATION_PHRASES.get(org, "with standard project structure")
            sentences.append(f"The codebase is organized {org_phrase}.")
        elif rule_output.structure_score >= 7:
            sentences.append("The codebase follows a clear organizational pattern.")
        elif rule_output.structure_score >= 4:
            sentences.append("Project organization is acceptable but could be cleaner.")
        
        # Sentence 4: Recruiter impression if available
        if ai_insights.recruiter_feedback and ai_insights.recruiter_feedback.overall_impression:
            # Use recruiter impression directly if available
            impression = ai_insights.recruiter_feedback.overall_impression.strip()
            if impression and not impression.endswith('.'):
                impression += '.'
            if impression:
                sentences.append(impression)
        
        # Sentence 5: Readiness assessment
        if final_scores.final_score >= 7.0:
            sentences.append("The project is ready for portfolio presentation and recruiter review.")
        elif final_scores.final_score >= 5.0:
            sentences.append("With targeted improvements, this project can be portfolio-ready.")
        else:
            sentences.append("Addressing the identified issues will significantly improve project presentation.")
        
        # Join and limit to 5 sentences
        return " ".join(sentences[:5])
    
    def _extract_strengths(
        self,
        rule_output: RuleEngineOutput,
        ai_insights: AIInsightsPayload,
    ) -> list[str]:
        """
        Extract strengths from rule engine and AI insights.
        
        Rules:
        - Derived only from rule engine positives and AI insight strengths
        - Action-oriented phrasing
        - Max 5 items
        """
        strengths: list[str] = []
        
        # Rule-based strengths (derived from high scores)
        if rule_output.documentation_score >= 7:
            strengths.append("Comprehensive documentation with clear project description")
        
        if rule_output.structure_score >= 7:
            strengths.append("Well-organized project structure with logical separation of concerns")
        
        if rule_output.configuration_score >= 7:
            strengths.append("Proper configuration files including license and dependency management")
        
        if rule_output.completeness_score >= 7:
            strengths.append("Complete project setup with all essential components")
        
        # AI-derived strengths
        if ai_insights.documentation_quality:
            for strength in ai_insights.documentation_quality.strengths[:2]:
                if strength and strength not in strengths:
                    strengths.append(strength)
        
        if ai_insights.code_clarity:
            for signal in ai_insights.code_clarity.maintainability_signals[:2]:
                if signal and signal not in strengths:
                    strengths.append(signal)
        
        if ai_insights.recruiter_feedback:
            for standout in ai_insights.recruiter_feedback.what_stands_out[:2]:
                if standout and standout not in strengths:
                    strengths.append(standout)
        
        # Deduplicate and limit
        seen = set()
        unique_strengths = []
        for s in strengths:
            normalized = s.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_strengths.append(s)
        
        return unique_strengths[:5]
    
    def _extract_improvements(
        self,
        rule_output: RuleEngineOutput,
        ai_insights: AIInsightsPayload,
    ) -> list[str]:
        """
        Extract improvement areas from issues and AI gaps.
        
        Rules:
        - Derived only from rule engine issues and AI-identified gaps/concerns
        - Actionable and constructive
        - Max 5 items
        """
        improvements: list[str] = []
        
        # Rule-based issues (directly from rule engine)
        for issue in rule_output.issues[:3]:
            if issue:
                improvements.append(issue)
        
        # AI-derived improvements
        if ai_insights.documentation_quality:
            for suggestion in ai_insights.documentation_quality.suggestions[:2]:
                if suggestion and suggestion not in improvements:
                    improvements.append(suggestion)
            for gap in ai_insights.documentation_quality.gaps[:1]:
                if gap and gap not in improvements:
                    improvements.append(f"Address: {gap}")
        
        if ai_insights.code_clarity:
            for concern in ai_insights.code_clarity.concerns[:2]:
                if concern and concern not in improvements:
                    improvements.append(concern)
        
        if ai_insights.tech_stack_analysis:
            for missing in ai_insights.tech_stack_analysis.missing_expectations[:1]:
                if missing:
                    improvements.append(f"Consider adding {missing}")
        
        if ai_insights.recruiter_feedback:
            for work in ai_insights.recruiter_feedback.what_needs_work[:2]:
                if work and work not in improvements:
                    improvements.append(work)
        
        # Deduplicate and limit
        seen = set()
        unique_improvements = []
        for imp in improvements:
            normalized = imp.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_improvements.append(imp)
        
        return unique_improvements[:5]
    
    def _generate_resume_bullets(
        self,
        repo_metadata: RepoMetadata,
        rule_output: RuleEngineOutput,
        ai_insights: AIInsightsPayload,
        strengths: list[str],
    ) -> list[str]:
        """
        Generate resume-ready bullet points.
        
        Rules:
        - Written in resume language
        - Start with strong action verbs
        - No buzzwords or exaggeration
        - Max 4 bullets
        - Must be directly supported by analysis
        """
        bullets: list[str] = []
        repo_name = repo_metadata.repo_name
        
        # Bullet 1: Tech stack description (if available)
        if ai_insights.tech_stack_analysis:
            tech = ai_insights.tech_stack_analysis
            if tech.primary_stack:
                stack_str = ", ".join(tech.primary_stack[:3])
                bullets.append(
                    f"Developed {repo_name} utilizing {stack_str}"
                )
        
        # Bullet 2: From strong structural signals
        if rule_output.structure_score >= 6:
            if ai_insights.code_clarity and ai_insights.code_clarity.organization == "well-structured":
                bullets.append(
                    "Architected a modular codebase with clear separation of concerns"
                )
            elif rule_output.structure_score >= 7:
                bullets.append(
                    "Designed an organized project structure following industry best practices"
                )
        
        # Bullet 3: From documentation quality
        if rule_output.documentation_score >= 6:
            if ai_insights.documentation_quality and ai_insights.documentation_quality.clarity == "high":
                bullets.append(
                    "Created comprehensive technical documentation including setup guides and usage examples"
                )
            elif rule_output.documentation_score >= 7:
                bullets.append(
                    "Authored detailed README documentation covering installation, usage, and features"
                )
        
        # Bullet 4: From identified strengths (transform to resume format)
        action_verbs = [
            "Implemented", "Designed", "Developed", "Engineered",
            "Built", "Created", "Established", "Constructed"
        ]
        
        for i, strength in enumerate(strengths[:2]):
            if len(bullets) >= 4:
                break
            
            # Check if strength already starts with an action verb
            starts_with_verb = any(strength.lower().startswith(v.lower()) for v in action_verbs)
            
            if starts_with_verb:
                # Use as-is but capitalize first letter
                bullet = strength[0].upper() + strength[1:]
            else:
                # Prepend action verb
                verb = action_verbs[i % len(action_verbs)]
                # Clean up the strength text
                cleaned = strength.rstrip('.')
                bullet = f"{verb} {cleaned.lower()}"
            
            if bullet not in bullets:
                bullets.append(bullet)
        
        # Bullet 5: Configuration/completeness based (fallback)
        if len(bullets) < 3 and rule_output.configuration_score >= 7:
            bullets.append(
                "Configured project with proper dependency management, licensing, and version control"
            )
        
        # Ensure all bullets are properly formatted
        formatted_bullets = []
        for bullet in bullets[:4]:
            # Remove trailing periods for resume consistency
            bullet = bullet.rstrip('.')
            # Capitalize first letter
            bullet = bullet[0].upper() + bullet[1:] if bullet else bullet
            formatted_bullets.append(bullet)
        
        return formatted_bullets[:4]


def get_report_generation_service() -> ReportGenerationService:
    """Factory function for dependency injection."""
    return ReportGenerationService()
