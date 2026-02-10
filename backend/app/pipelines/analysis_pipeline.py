"""
Analysis Pipeline Orchestrator

Phase 3: Full evaluation pipeline combining:
1. Repository ingestion (Phase 1)
2. Rule-based evaluation (Phase 2)
3. AI-assisted analysis (Phase 3)
4. Final report generation

This module sequences all evaluation steps and produces
the complete FinalReport output.
"""

import os
from typing import Any

from app.services.ingestion_service import (
    IngestionService,
    IngestedRepository,
    IngestionError,
)
from app.services.evaluation_service import (
    EvaluationService,
    EvaluationResult,
)
from app.services.ai_analysis_service import AIAnalysisService
from app.services.hybrid_scoring_service import HybridScoringService
from app.services.report_generation_service import ReportGenerationService
from app.schemas.models import (
    RuleEvaluationResult,
    AIInsightResult,
    FinalReport,
    CombinedAIInsights,
    AIAnalysisError,
    HybridScoringResult,
    HybridScoringError,
    ReportGenerationInput,
    ReportGenerationOutput,
    ReportGenerationError,
    RepoMetadata,
    RuleEngineOutput,
    AIInsightsPayload,
    FinalScores,
)


class PipelineError(Exception):
    """Raised when the analysis pipeline encounters an error."""
    
    def __init__(self, error_type: str, message: str, details: str | None = None):
        self.error_type = error_type
        self.message = message
        self.details = details
        super().__init__(message)
    
    def to_dict(self) -> dict:
        """Convert to error response format."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "details": self.details,
            }
        }


class AnalysisPipeline:
    """
    Full analysis pipeline orchestrator.
    
    Coordinates all three phases:
    - Phase 1: Repository ingestion
    - Phase 2: Rule-based evaluation (deterministic)
    - Phase 3: AI-assisted qualitative analysis
    - Phase 4: Hybrid scoring
    - Phase 5: Report generation
    
    Produces a combined FinalReport.
    """
    
    def __init__(
        self,
        github_token: str | None = None,
        gemini_api_key: str | None = None,
    ):
        """
        Initialize the analysis pipeline.
        
        Args:
            github_token: Optional GitHub token for API access
            gemini_api_key: Google Gemini API key for AI analysis
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # Initialize services
        self.ingestion_service = IngestionService(github_token=self.github_token)
        self.evaluation_service = EvaluationService()
        self.hybrid_scoring_service = HybridScoringService()
        self.report_generation_service = ReportGenerationService()
        
        # AI service initialized lazily (requires API key)
        self._ai_service: AIAnalysisService | None = None
    
    @property
    def ai_service(self) -> AIAnalysisService:
        """Lazy initialization of AI service."""
        if self._ai_service is None:
            if not self.gemini_api_key:
                raise PipelineError(
                    error_type="CONFIGURATION_ERROR",
                    message="Gemini API key is required for AI analysis",
                    details="Set GEMINI_API_KEY environment variable or provide gemini_api_key parameter",
                )
            self._ai_service = AIAnalysisService(api_key=self.gemini_api_key)
        return self._ai_service
    
    async def run_full_analysis(
        self,
        github_url: str,
        include_ai: bool = True,
    ) -> FinalReport:
        """
        Execute the complete analysis pipeline.
        
        Steps:
        1. Ingest repository data
        2. Run rule-based evaluation
        3. Run AI-assisted analysis (parallel)
        4. Combine into FinalReport
        
        Args:
            github_url: Public GitHub repository URL
            include_ai: Whether to include AI analysis (default: True)
            
        Returns:
            FinalReport with all evaluation results
            
        Raises:
            PipelineError: If critical errors occur during processing
        """
        # Phase 1: Repository Ingestion
        ingest_result = await self.ingestion_service.ingest(github_url)
        
        if isinstance(ingest_result, IngestionError):
            raise PipelineError(
                error_type=ingest_result.error_type,
                message=ingest_result.message,
                details=ingest_result.details,
            )
        
        repository: IngestedRepository = ingest_result
        
        # Phase 2: Rule-Based Evaluation
        rule_result: EvaluationResult = self.evaluation_service.evaluate(repository)
        
        # Convert to Pydantic model
        rule_evaluation = RuleEvaluationResult(
            documentation_score=rule_result.documentation_score,
            structure_score=rule_result.structure_score,
            configuration_score=rule_result.configuration_score,
            completeness_score=rule_result.completeness_score,
            issues=rule_result.issues,
        )
        
        # Phase 3: AI-Assisted Analysis
        ai_insights, combined_ai = await self._run_ai_analysis(
            repository=repository,
            rule_result=rule_result,
            include_ai=include_ai,
        )
        
        # Phase 4: Hybrid Scoring
        overall_score, hybrid_result = self._calculate_hybrid_score(rule_result, combined_ai)
        
        # Phase 5: Report Generation
        report_output = self._generate_report(
            repository=repository,
            rule_result=rule_result,
            combined_ai=combined_ai,
            hybrid_result=hybrid_result,
        )
        
        # Handle potential report generation error
        if isinstance(report_output, ReportGenerationOutput):
            return FinalReport(
                repo_name=repository.repo_name,
                overall_score=overall_score,
                rule_evaluation=rule_evaluation,
                ai_insights=ai_insights,
                resume_bullets=report_output.resume_bullets,
                executive_summary=report_output.summary,
                strengths=report_output.strengths,
                improvements=report_output.improvements,
            )
        else:
            # Fallback on report generation error
            return FinalReport(
                repo_name=repository.repo_name,
                overall_score=overall_score,
                rule_evaluation=rule_evaluation,
                ai_insights=ai_insights,
                resume_bullets=[],
                executive_summary=f"Analysis complete for {repository.repo_name}.",
                strengths=[],
                improvements=rule_result.issues[:5],
            )
    
    async def _run_ai_analysis(
        self,
        repository: IngestedRepository,
        rule_result: EvaluationResult,
        include_ai: bool,
    ) -> tuple[AIInsightResult, CombinedAIInsights | None]:
        """
        Run Phase 3 AI analysis and convert to AIInsightResult.
        
        If AI is disabled or fails, returns a basic result.
        
        Returns:
            Tuple of (AIInsightResult for user display, CombinedAIInsights for scoring)
        """
        if not include_ai or not self.gemini_api_key:
            return AIInsightResult(
                summary="AI analysis was not performed.",
                strengths=[],
                improvements=[],
            ), None
        
        try:
            # Prepare rule engine summary for AI context
            rule_summary = {
                "documentation_score": rule_result.documentation_score,
                "structure_score": rule_result.structure_score,
                "configuration_score": rule_result.configuration_score,
                "completeness_score": rule_result.completeness_score,
                "issues": rule_result.issues,
            }
            
            # Run all AI analyses in parallel
            combined: CombinedAIInsights = await self.ai_service.run_all_analyses(
                repo_name=repository.repo_name,
                owner=repository.owner,
                languages=repository.languages,
                files=repository.files,
                readme=repository.readme,
                rule_engine_summary=rule_summary,
            )
            
            # Convert combined results to AIInsightResult, return both for hybrid scoring
            return self._synthesize_ai_insights(combined, repository), combined
            
        except Exception as e:
            # On AI failure, return basic result with error note
            return AIInsightResult(
                summary=f"AI analysis encountered an error: {str(e)}",
                strengths=[],
                improvements=[],
            ), None
    
    def _synthesize_ai_insights(
        self,
        combined: CombinedAIInsights,
        repository: IngestedRepository,
    ) -> AIInsightResult:
        """
        Synthesize combined AI analysis results into AIInsightResult.
        
        Aggregates documentation, code clarity, tech stack, and recruiter feedback.
        """
        strengths: list[str] = []
        improvements: list[str] = []
        summary_parts: list[str] = []
        
        # Extract from documentation analysis
        if combined.documentation:
            doc = combined.documentation
            strengths.extend(doc.strengths)
            improvements.extend(doc.suggestions)
            if doc.clarity == "high":
                summary_parts.append("Documentation is clear and comprehensive.")
            elif doc.clarity == "low":
                summary_parts.append("Documentation needs significant improvement.")
        
        # Extract from code clarity analysis
        if combined.code_clarity:
            code = combined.code_clarity
            strengths.extend(code.maintainability_signals)
            if code.concerns:
                improvements.extend(code.concerns)
            if code.organization == "well-structured":
                summary_parts.append("Project structure is well-organized.")
            elif code.organization == "poor":
                summary_parts.append("Project structure could be better organized.")
        
        # Extract from tech stack analysis
        if combined.tech_stack:
            tech = combined.tech_stack
            if tech.primary_stack:
                stack_str = ", ".join(tech.primary_stack[:3])
                summary_parts.append(f"Uses {stack_str}.")
            if tech.missing_expectations:
                improvements.extend([
                    f"Consider adding {item}" for item in tech.missing_expectations
                ])
        
        # Extract from recruiter feedback
        if combined.recruiter_feedback:
            feedback = combined.recruiter_feedback
            strengths.extend(feedback.what_stands_out)
            improvements.extend(feedback.what_needs_work)
            if feedback.overall_impression:
                summary_parts.insert(0, feedback.overall_impression)
        
        # Note any AI errors
        if combined.errors:
            error_count = len(combined.errors)
            summary_parts.append(
                f"Note: {error_count} AI analysis component(s) encountered errors."
            )
        
        # Build summary
        summary = " ".join(summary_parts) if summary_parts else (
            f"Analysis complete for {repository.repo_name}."
        )
        
        # Deduplicate and limit lists
        strengths = list(dict.fromkeys(strengths))[:10]
        improvements = list(dict.fromkeys(improvements))[:10]
        
        return AIInsightResult(
            summary=summary,
            strengths=strengths,
            improvements=improvements,
        )
    
    def _calculate_hybrid_score(
        self,
        rule_result: EvaluationResult,
        combined_ai: CombinedAIInsights | None,
    ) -> tuple[float, HybridScoringResult | None]:
        """
        Calculate overall score using the Hybrid Scoring Engine (Phase 4).
        
        Combines rule-based scores (40% weight) with quantified AI signals (60% weight).
        If AI signals are missing, uses only rule-based scores.
        
        Returns:
            Tuple of (score scaled to 0-100, HybridScoringResult or None)
        """
        result = self.hybrid_scoring_service.compute_hybrid_score(
            rule_result=rule_result,
            ai_insights=combined_ai,
        )
        
        if isinstance(result, HybridScoringError):
            # Fallback to simple average if hybrid scoring fails
            weighted = (
                rule_result.documentation_score * 0.30 +
                rule_result.structure_score * 0.25 +
                rule_result.configuration_score * 0.20 +
                rule_result.completeness_score * 0.25
            )
            return round(weighted * 10, 1), None
        
        # Scale from 0-10 to 0-100 for FinalReport compatibility
        return round(result.final_score * 10, 1), result
    
    def _generate_report(
        self,
        repository: IngestedRepository,
        rule_result: EvaluationResult,
        combined_ai: CombinedAIInsights | None,
        hybrid_result: HybridScoringResult | None,
    ) -> ReportGenerationOutput | ReportGenerationError:
        """
        Generate Phase 5 report using ReportGenerationService.
        
        Constructs the consolidated input payload and delegates to
        the report generation service.
        
        Returns:
            ReportGenerationOutput with summary, strengths, improvements, resume_bullets
            or ReportGenerationError on failure
        """
        # Build consolidated input payload
        repo_metadata = RepoMetadata(
            repo_name=repository.repo_name,
            owner=repository.owner,
        )
        
        rule_engine_output = RuleEngineOutput(
            documentation_score=rule_result.documentation_score,
            structure_score=rule_result.structure_score,
            configuration_score=rule_result.configuration_score,
            completeness_score=rule_result.completeness_score,
            issues=rule_result.issues,
        )
        
        # Build AI insights payload
        ai_insights_payload = AIInsightsPayload(
            documentation_quality=combined_ai.documentation if combined_ai else None,
            code_clarity=combined_ai.code_clarity if combined_ai else None,
            tech_stack_analysis=combined_ai.tech_stack if combined_ai else None,
            recruiter_feedback=combined_ai.recruiter_feedback if combined_ai else None,
        )
        
        # Build final scores payload
        if hybrid_result:
            final_scores = FinalScores(
                rule_composite_score=hybrid_result.rule_composite_score,
                ai_signal_score=hybrid_result.ai_signal_score,
                final_score=hybrid_result.final_score,
            )
        else:
            # Fallback if hybrid scoring failed
            avg_score = (
                rule_result.documentation_score +
                rule_result.structure_score +
                rule_result.configuration_score +
                rule_result.completeness_score
            ) / 4
            final_scores = FinalScores(
                rule_composite_score=avg_score,
                ai_signal_score=avg_score,
                final_score=avg_score,
            )
        
        # Construct full input
        report_input = ReportGenerationInput(
            repo_metadata=repo_metadata,
            rule_engine_output=rule_engine_output,
            ai_insights=ai_insights_payload,
            final_scores=final_scores,
        )
        
        # Generate report and return result (can be output or error)
        return self.report_generation_service.generate_report(report_input)
    
    def _generate_resume_bullets(
        self,
        repository: IngestedRepository,
        rule_result: EvaluationResult,
        ai_insights: AIInsightResult,
    ) -> list[str]:
        """
        Generate resume-ready bullet points.
        
        Combines repository metadata, tech stack, and AI insights
        to create professional project descriptions.
        """
        bullets: list[str] = []
        
        # Primary languages
        if repository.languages:
            top_langs = sorted(
                repository.languages.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            lang_names = [lang for lang, _ in top_langs]
            
            if len(lang_names) == 1:
                tech_str = lang_names[0]
            else:
                tech_str = ", ".join(lang_names[:-1]) + f" and {lang_names[-1]}"
            
            bullets.append(
                f"Built {repository.repo_name} using {tech_str}"
            )
        
        # File count as project scale indicator
        file_count = len([f for f in repository.files if f.get("type") == "file"])
        if file_count > 20:
            bullets.append(
                f"Developed and maintained a codebase with {file_count}+ files"
            )
        
        # Add strength-based bullets from AI
        if ai_insights.strengths:
            for strength in ai_insights.strengths[:2]:
                # Clean up for resume format
                if not strength.endswith("."):
                    strength += "."
                bullets.append(strength)
        
        # Documentation quality indicator
        if rule_result.documentation_score >= 7:
            bullets.append(
                "Created comprehensive documentation including README and setup guides"
            )
        
        # Test presence indicator
        has_tests = any(
            "test" in f.get("path", "").lower() 
            for f in repository.files
        )
        if has_tests:
            bullets.append(
                "Implemented testing infrastructure for code quality assurance"
            )
        
        return bullets[:5]  # Limit to 5 bullets
