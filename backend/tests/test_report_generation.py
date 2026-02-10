"""
Unit Tests for Report Generation Service (Phase 5)

Tests the ReportGenerationService for:
1. Determinism: Same input → Same output
2. Proper derivation from inputs (no hallucination)
3. Max item limits enforcement
4. Error handling for missing/invalid inputs
5. Resume bullet quality
"""

import pytest
from app.services.report_generation_service import ReportGenerationService
from app.schemas.models import (
    ReportGenerationInput,
    ReportGenerationOutput,
    ReportGenerationError,
    RepoMetadata,
    RuleEngineOutput,
    AIInsightsPayload,
    FinalScores,
    DocumentationQualityResult,
    CodeClarityResult,
    TechStackResult,
    RecruiterFeedbackResult,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service():
    """Create ReportGenerationService instance."""
    return ReportGenerationService()


@pytest.fixture
def sample_repo_metadata():
    """Sample repository metadata."""
    return RepoMetadata(
        repo_name="test-project",
        owner="testuser",
    )


@pytest.fixture
def sample_rule_output_high():
    """Sample high-scoring rule engine output."""
    return RuleEngineOutput(
        documentation_score=8,
        structure_score=9,
        configuration_score=10,
        completeness_score=8,
        issues=[],
    )


@pytest.fixture
def sample_rule_output_low():
    """Sample low-scoring rule engine output with issues."""
    return RuleEngineOutput(
        documentation_score=3,
        structure_score=4,
        configuration_score=3,
        completeness_score=3,
        issues=[
            "README is missing",
            "No .gitignore file found",
            "No LICENSE file found",
            "No dependency file found",
        ],
    )


@pytest.fixture
def sample_ai_insights_full():
    """Sample complete AI insights."""
    return AIInsightsPayload(
        documentation_quality=DocumentationQualityResult(
            clarity="high",
            strengths=["Clear installation instructions", "Good examples"],
            gaps=["Missing API documentation"],
            suggestions=["Add API reference section"],
        ),
        code_clarity=CodeClarityResult(
            organization="well-structured",
            naming_consistency="high",
            maintainability_signals=["Modular architecture", "Separation of concerns"],
            concerns=[],
        ),
        tech_stack_analysis=TechStackResult(
            primary_stack=["Python", "FastAPI"],
            supporting_tools=["pytest", "Docker"],
            usage_explanation="A modern Python web service using FastAPI framework",
            missing_expectations=[],
        ),
        recruiter_feedback=RecruiterFeedbackResult(
            overall_impression="A well-organized project demonstrating solid engineering practices.",
            what_stands_out=["Clean code structure", "Comprehensive testing"],
            what_needs_work=[],
        ),
    )


@pytest.fixture
def sample_ai_insights_minimal():
    """Sample minimal AI insights (some components missing)."""
    return AIInsightsPayload(
        documentation_quality=DocumentationQualityResult(
            clarity="medium",
            strengths=["Basic README present"],
            gaps=["No usage examples"],
            suggestions=["Add usage examples"],
        ),
        code_clarity=None,
        tech_stack_analysis=None,
        recruiter_feedback=None,
    )


@pytest.fixture
def sample_final_scores_high():
    """Sample high final scores."""
    return FinalScores(
        rule_composite_score=8.75,
        ai_signal_score=8.5,
        final_score=8.6,
    )


@pytest.fixture
def sample_final_scores_low():
    """Sample low final scores."""
    return FinalScores(
        rule_composite_score=3.25,
        ai_signal_score=4.0,
        final_score=3.7,
    )


@pytest.fixture
def full_input_high(
    sample_repo_metadata,
    sample_rule_output_high,
    sample_ai_insights_full,
    sample_final_scores_high,
):
    """Complete input with high scores."""
    return ReportGenerationInput(
        repo_metadata=sample_repo_metadata,
        rule_engine_output=sample_rule_output_high,
        ai_insights=sample_ai_insights_full,
        final_scores=sample_final_scores_high,
    )


@pytest.fixture
def full_input_low(
    sample_repo_metadata,
    sample_rule_output_low,
    sample_ai_insights_minimal,
    sample_final_scores_low,
):
    """Complete input with low scores."""
    return ReportGenerationInput(
        repo_metadata=sample_repo_metadata,
        rule_engine_output=sample_rule_output_low,
        ai_insights=sample_ai_insights_minimal,
        final_scores=sample_final_scores_low,
    )


# ============================================================================
# Test: Determinism (Same Input → Same Output)
# ============================================================================

class TestDeterminism:
    """Tests to verify deterministic behavior."""
    
    def test_same_input_produces_same_output(self, service, full_input_high):
        """Same input should always produce identical output."""
        result1 = service.generate_report(full_input_high)
        result2 = service.generate_report(full_input_high)
        
        assert isinstance(result1, ReportGenerationOutput)
        assert isinstance(result2, ReportGenerationOutput)
        assert result1.summary == result2.summary
        assert result1.strengths == result2.strengths
        assert result1.improvements == result2.improvements
        assert result1.resume_bullets == result2.resume_bullets
    
    def test_different_inputs_produce_different_outputs(
        self, service, full_input_high, full_input_low
    ):
        """Different inputs should produce different outputs."""
        result_high = service.generate_report(full_input_high)
        result_low = service.generate_report(full_input_low)
        
        assert isinstance(result_high, ReportGenerationOutput)
        assert isinstance(result_low, ReportGenerationOutput)
        
        # Summaries should be different due to different score levels
        assert result_high.summary != result_low.summary
        
        # Low scoring should have more improvements
        assert len(result_low.improvements) > len(result_high.improvements)


# ============================================================================
# Test: Executive Summary Generation
# ============================================================================

class TestExecutiveSummary:
    """Tests for executive summary generation."""
    
    def test_summary_length(self, service, full_input_high):
        """Summary should be 3-5 sentences."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        # Count sentences (approximation by counting periods)
        sentence_count = result.summary.count('.')
        assert 3 <= sentence_count <= 6  # Allow some flexibility
    
    def test_summary_no_numeric_scores(self, service, full_input_high):
        """Summary should not contain raw numeric scores."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        # Check for score patterns like "8.6" or "8/10"
        import re
        score_pattern = r'\b\d+\.?\d*/10\b|\b\d+\.\d+\b'
        matches = re.findall(score_pattern, result.summary)
        assert len(matches) == 0, f"Summary contains numeric scores: {matches}"
    
    def test_summary_contains_repo_name(self, service, full_input_high):
        """Summary should mention the repository name."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        assert "test-project" in result.summary
    
    def test_high_score_positive_summary(self, service, full_input_high):
        """High scoring project should have positive summary."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        # Should contain positive language
        positive_terms = ["well-prepared", "solid", "strong", "ready"]
        has_positive = any(term in result.summary.lower() for term in positive_terms)
        assert has_positive
    
    def test_low_score_improvement_summary(self, service, full_input_low):
        """Low scoring project should indicate need for improvement."""
        result = service.generate_report(full_input_low)
        
        assert isinstance(result, ReportGenerationOutput)
        
        # Should indicate need for work
        improvement_terms = ["requires", "improvement", "needs", "addressing"]
        has_improvement = any(term in result.summary.lower() for term in improvement_terms)
        assert has_improvement


# ============================================================================
# Test: Strengths Extraction
# ============================================================================

class TestStrengths:
    """Tests for strengths extraction."""
    
    def test_max_five_strengths(self, service, full_input_high):
        """Should return maximum 5 strengths."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        assert len(result.strengths) <= 5
    
    def test_strengths_derived_from_input(self, service, full_input_high):
        """Strengths should be derived from rule scores and AI insights."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        assert len(result.strengths) > 0
        
        # All strengths should exist (not empty strings)
        for strength in result.strengths:
            assert strength.strip() != ""
    
    def test_no_strengths_when_all_low(self, service, full_input_low):
        """Low scoring project may have fewer/no rule-derived strengths."""
        result = service.generate_report(full_input_low)
        
        assert isinstance(result, ReportGenerationOutput)
        # AI insights may still provide some strengths even with low scores
        assert isinstance(result.strengths, list)
    
    def test_no_duplicate_strengths(self, service, full_input_high):
        """Strengths should not have duplicates."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        # Normalize for comparison
        normalized = [s.lower().strip() for s in result.strengths]
        assert len(normalized) == len(set(normalized))


# ============================================================================
# Test: Improvements Extraction
# ============================================================================

class TestImprovements:
    """Tests for improvements extraction."""
    
    def test_max_five_improvements(self, service, full_input_low):
        """Should return maximum 5 improvements."""
        result = service.generate_report(full_input_low)
        
        assert isinstance(result, ReportGenerationOutput)
        assert len(result.improvements) <= 5
    
    def test_improvements_derived_from_issues(self, service, full_input_low):
        """Improvements should include rule engine issues."""
        result = service.generate_report(full_input_low)
        
        assert isinstance(result, ReportGenerationOutput)
        assert len(result.improvements) > 0
        
        # Should contain at least some of the original issues
        original_issues = {"readme", "gitignore", "license", "dependency"}
        found = any(
            any(issue in imp.lower() for issue in original_issues)
            for imp in result.improvements
        )
        assert found
    
    def test_improvements_actionable(self, service, full_input_low):
        """Improvements should be actionable statements."""
        result = service.generate_report(full_input_low)
        
        assert isinstance(result, ReportGenerationOutput)
        
        # Should not be empty strings
        for improvement in result.improvements:
            assert improvement.strip() != ""
            assert len(improvement) > 10  # Should be meaningful
    
    def test_no_duplicate_improvements(self, service, full_input_low):
        """Improvements should not have duplicates."""
        result = service.generate_report(full_input_low)
        
        assert isinstance(result, ReportGenerationOutput)
        
        normalized = [i.lower().strip() for i in result.improvements]
        assert len(normalized) == len(set(normalized))


# ============================================================================
# Test: Resume Bullets Generation
# ============================================================================

class TestResumeBullets:
    """Tests for resume bullet generation."""
    
    def test_max_four_bullets(self, service, full_input_high):
        """Should return maximum 4 resume bullets."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        assert len(result.resume_bullets) <= 4
    
    def test_bullets_start_with_action_verb(self, service, full_input_high):
        """Resume bullets should start with capitalized word (action verb)."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        for bullet in result.resume_bullets:
            # First character should be uppercase
            assert bullet[0].isupper(), f"Bullet should start with capital: {bullet}"
    
    def test_bullets_no_trailing_periods(self, service, full_input_high):
        """Resume bullets should not end with periods (resume convention)."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        for bullet in result.resume_bullets:
            assert not bullet.endswith('.'), f"Bullet should not end with period: {bullet}"
    
    def test_bullets_concise(self, service, full_input_high):
        """Resume bullets should be concise (not too long)."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        for bullet in result.resume_bullets:
            # Reasonable length for resume bullets (under 150 chars)
            assert len(bullet) <= 150, f"Bullet too long: {bullet}"
    
    def test_bullets_no_buzzwords(self, service, full_input_high):
        """Resume bullets should avoid buzzwords."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        buzzwords = ["synergy", "leverage", "paradigm", "disrupt", "revolutionary"]
        for bullet in result.resume_bullets:
            for buzzword in buzzwords:
                assert buzzword not in bullet.lower(), f"Found buzzword '{buzzword}' in: {bullet}"


# ============================================================================
# Test: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_missing_repo_name_error(self, service):
        """Should return error when repo name is missing."""
        input_data = ReportGenerationInput(
            repo_metadata=RepoMetadata(repo_name="", owner="testuser"),
            rule_engine_output=RuleEngineOutput(
                documentation_score=5,
                structure_score=5,
                configuration_score=5,
                completeness_score=5,
                issues=[],
            ),
            ai_insights=AIInsightsPayload(),
            final_scores=FinalScores(
                rule_composite_score=5.0,
                ai_signal_score=5.0,
                final_score=5.0,
            ),
        )
        
        result = service.generate_report(input_data)
        
        assert isinstance(result, ReportGenerationError)
        assert result.error.type == "MISSING_INPUT"
    
    def test_handles_empty_ai_insights(self, service, sample_repo_metadata, sample_rule_output_high, sample_final_scores_high):
        """Should handle empty AI insights gracefully."""
        input_data = ReportGenerationInput(
            repo_metadata=sample_repo_metadata,
            rule_engine_output=sample_rule_output_high,
            ai_insights=AIInsightsPayload(),  # All None
            final_scores=sample_final_scores_high,
        )
        
        result = service.generate_report(input_data)
        
        # Should still produce valid output
        assert isinstance(result, ReportGenerationOutput)
        assert len(result.summary) > 0


# ============================================================================
# Test: Output Quality Gates
# ============================================================================

class TestQualityGates:
    """Tests for output quality requirements."""
    
    def test_summary_readable_in_30_seconds(self, service, full_input_high):
        """Summary should be short enough to read in 30 seconds."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        # Average reading speed ~200-250 words/min
        # 30 seconds = ~100-125 words max
        word_count = len(result.summary.split())
        assert word_count <= 150, f"Summary too long: {word_count} words"
    
    def test_no_raw_scores_in_output(self, service, full_input_high):
        """No raw numeric scores should appear in text fields."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        import re
        score_pattern = r'\b[0-9]+/10\b|\b[0-9]+\.[0-9]+/10\b'
        
        # Check all text fields
        all_text = (
            result.summary +
            " ".join(result.strengths) +
            " ".join(result.improvements) +
            " ".join(result.resume_bullets)
        )
        
        matches = re.findall(score_pattern, all_text)
        assert len(matches) == 0, f"Found raw scores: {matches}"
    
    def test_professional_tone(self, service, full_input_high):
        """Output should maintain professional tone (no slang)."""
        result = service.generate_report(full_input_high)
        
        assert isinstance(result, ReportGenerationOutput)
        
        slang_terms = ["awesome", "amazing", "super", "totally", "gonna", "wanna"]
        all_text = (
            result.summary.lower() +
            " ".join(result.strengths).lower() +
            " ".join(result.improvements).lower()
        )
        
        for term in slang_terms:
            assert term not in all_text, f"Found unprofessional term: {term}"
