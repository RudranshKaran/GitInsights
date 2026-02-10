"""
Unit Tests for Hybrid Scoring Service (Phase 4)

Tests verify:
1. Determinism: Same input → Same output
2. Rule composite computation accuracy
3. AI signal quantification with fixed mappings
4. Missing signal handling and weight re-normalization
5. Error responses for invalid/missing rule scores
6. Boundary conditions and edge cases
"""

import pytest
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.evaluation_service import EvaluationResult
from app.services.hybrid_scoring_service import (
    HybridScoringService,
    QuantifiedSignals,
    CLARITY_MAPPING,
    ORGANIZATION_MAPPING,
    NAMING_MAPPING,
)
from app.schemas.models import (
    CombinedAIInsights,
    DocumentationQualityResult,
    CodeClarityResult,
    TechStackResult,
    RecruiterFeedbackResult,
    HybridScoringResult,
    HybridScoringError,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def scoring_service() -> HybridScoringService:
    """Default hybrid scoring service with standard weights."""
    return HybridScoringService()


@pytest.fixture
def perfect_rule_result() -> EvaluationResult:
    """Rule result with perfect scores (all 10s)."""
    return EvaluationResult(
        documentation_score=10,
        structure_score=10,
        configuration_score=10,
        completeness_score=10,
        issues=[],
    )


@pytest.fixture
def average_rule_result() -> EvaluationResult:
    """Rule result with average scores."""
    return EvaluationResult(
        documentation_score=7,
        structure_score=6,
        configuration_score=8,
        completeness_score=5,
        issues=["Some issue"],
    )


@pytest.fixture
def low_rule_result() -> EvaluationResult:
    """Rule result with low scores."""
    return EvaluationResult(
        documentation_score=2,
        structure_score=3,
        configuration_score=1,
        completeness_score=2,
        issues=["Many issues"],
    )


@pytest.fixture
def high_ai_insights() -> CombinedAIInsights:
    """AI insights with all high/well-structured signals."""
    return CombinedAIInsights(
        documentation=DocumentationQualityResult(
            clarity="high",
            strengths=["Good docs"],
            gaps=[],
            suggestions=[],
        ),
        code_clarity=CodeClarityResult(
            organization="well-structured",
            naming_consistency="high",
            maintainability_signals=["Clean code"],
            concerns=[],
        ),
        tech_stack=TechStackResult(
            primary_stack=["Python"],
            supporting_tools=["pytest"],
            usage_explanation="Uses Python",
            missing_expectations=[],
        ),
        recruiter_feedback=RecruiterFeedbackResult(
            overall_impression="Good project",
            what_stands_out=["Quality"],
            what_needs_work=[],
        ),
        errors=[],
    )


@pytest.fixture
def medium_ai_insights() -> CombinedAIInsights:
    """AI insights with medium signals."""
    return CombinedAIInsights(
        documentation=DocumentationQualityResult(
            clarity="medium",
            strengths=[],
            gaps=["Some gaps"],
            suggestions=["Improve docs"],
        ),
        code_clarity=CodeClarityResult(
            organization="acceptable",
            naming_consistency="medium",
            maintainability_signals=[],
            concerns=["Some concerns"],
        ),
        tech_stack=None,
        recruiter_feedback=None,
        errors=[],
    )


@pytest.fixture
def low_ai_insights() -> CombinedAIInsights:
    """AI insights with low/poor signals."""
    return CombinedAIInsights(
        documentation=DocumentationQualityResult(
            clarity="low",
            strengths=[],
            gaps=["Major gaps"],
            suggestions=["Rewrite docs"],
        ),
        code_clarity=CodeClarityResult(
            organization="poor",
            naming_consistency="low",
            maintainability_signals=[],
            concerns=["Many concerns"],
        ),
        tech_stack=None,
        recruiter_feedback=None,
        errors=[],
    )


# ============================================================================
# Determinism Tests
# ============================================================================

class TestDeterminism:
    """Verify same input always produces same output."""
    
    def test_same_input_same_output(
        self,
        scoring_service: HybridScoringService,
        average_rule_result: EvaluationResult,
        medium_ai_insights: CombinedAIInsights,
    ):
        """Same inputs should produce identical outputs."""
        result1 = scoring_service.compute_hybrid_score(
            average_rule_result, medium_ai_insights
        )
        result2 = scoring_service.compute_hybrid_score(
            average_rule_result, medium_ai_insights
        )
        
        assert isinstance(result1, HybridScoringResult)
        assert isinstance(result2, HybridScoringResult)
        assert result1.rule_composite_score == result2.rule_composite_score
        assert result1.ai_signal_score == result2.ai_signal_score
        assert result1.final_score == result2.final_score
    
    def test_multiple_runs_identical(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
        high_ai_insights: CombinedAIInsights,
    ):
        """Multiple runs should be identical (determinism guarantee)."""
        results = [
            scoring_service.compute_hybrid_score(
                perfect_rule_result, high_ai_insights
            )
            for _ in range(10)
        ]
        
        # All results should be HybridScoringResult
        for result in results:
            assert isinstance(result, HybridScoringResult)
        
        # All results should be identical to the first
        first = results[0]
        assert isinstance(first, HybridScoringResult)  # Type narrowing for type checker
        
        for result in results[1:]:
            assert isinstance(result, HybridScoringResult)  # Type narrowing
            assert result.final_score == first.final_score
            assert result.rule_composite_score == first.rule_composite_score
            assert result.ai_signal_score == first.ai_signal_score


# ============================================================================
# Rule Composite Score Tests
# ============================================================================

class TestRuleCompositeScore:
    """Test rule-based composite score computation."""
    
    def test_perfect_scores(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
    ):
        """Perfect scores should produce composite of 10."""
        result = scoring_service.compute_hybrid_score(
            perfect_rule_result, None
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.rule_composite_score == 10.0
    
    def test_average_scores(
        self,
        scoring_service: HybridScoringService,
        average_rule_result: EvaluationResult,
    ):
        """Average scores: (7+6+8+5)/4 = 6.5"""
        result = scoring_service.compute_hybrid_score(
            average_rule_result, None
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.rule_composite_score == 6.5
    
    def test_low_scores(
        self,
        scoring_service: HybridScoringService,
        low_rule_result: EvaluationResult,
    ):
        """Low scores: (2+3+1+2)/4 = 2.0"""
        result = scoring_service.compute_hybrid_score(
            low_rule_result, None
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.rule_composite_score == 2.0
    
    def test_zero_scores(self, scoring_service: HybridScoringService):
        """Zero scores should produce composite of 0."""
        rule_result = EvaluationResult(
            documentation_score=0,
            structure_score=0,
            configuration_score=0,
            completeness_score=0,
            issues=[],
        )
        
        result = scoring_service.compute_hybrid_score(rule_result, None)
        
        assert isinstance(result, HybridScoringResult)
        assert result.rule_composite_score == 0.0


# ============================================================================
# AI Signal Quantification Tests
# ============================================================================

class TestAISignalQuantification:
    """Test AI signal to numeric conversion."""
    
    def test_high_signals(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
        high_ai_insights: CombinedAIInsights,
    ):
        """High/well-structured signals should produce score of 9."""
        result = scoring_service.compute_hybrid_score(
            perfect_rule_result, high_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        # (9 + 9 + 9) / 3 = 9.0
        assert result.ai_signal_score == 9.0
    
    def test_medium_signals(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
        medium_ai_insights: CombinedAIInsights,
    ):
        """Medium/acceptable signals should produce score of 6."""
        result = scoring_service.compute_hybrid_score(
            perfect_rule_result, medium_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        # (6 + 6 + 6) / 3 = 6.0
        assert result.ai_signal_score == 6.0
    
    def test_low_signals(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
        low_ai_insights: CombinedAIInsights,
    ):
        """Low/poor signals should produce score of 3."""
        result = scoring_service.compute_hybrid_score(
            perfect_rule_result, low_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        # (3 + 3 + 3) / 3 = 3.0
        assert result.ai_signal_score == 3.0
    
    def test_mapping_values(self):
        """Verify fixed mapping table values."""
        assert CLARITY_MAPPING["low"] == 3.0
        assert CLARITY_MAPPING["medium"] == 6.0
        assert CLARITY_MAPPING["high"] == 9.0
        
        assert ORGANIZATION_MAPPING["poor"] == 3.0
        assert ORGANIZATION_MAPPING["acceptable"] == 6.0
        assert ORGANIZATION_MAPPING["well-structured"] == 9.0
        
        assert NAMING_MAPPING["low"] == 3.0
        assert NAMING_MAPPING["medium"] == 6.0
        assert NAMING_MAPPING["high"] == 9.0


# ============================================================================
# Hybrid Score Computation Tests
# ============================================================================

class TestHybridScoreComputation:
    """Test final weighted hybrid score calculation."""
    
    def test_perfect_hybrid_score(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
        high_ai_insights: CombinedAIInsights,
    ):
        """Perfect rules (10) + high AI (9) = 0.4*10 + 0.6*9 = 9.4"""
        result = scoring_service.compute_hybrid_score(
            perfect_rule_result, high_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.final_score == 9.4
    
    def test_average_hybrid_score(
        self,
        scoring_service: HybridScoringService,
        average_rule_result: EvaluationResult,
        medium_ai_insights: CombinedAIInsights,
    ):
        """Average rules (6.5) + medium AI (6) = 0.4*6.5 + 0.6*6 = 6.2"""
        result = scoring_service.compute_hybrid_score(
            average_rule_result, medium_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.final_score == 6.2
    
    def test_low_hybrid_score(
        self,
        scoring_service: HybridScoringService,
        low_rule_result: EvaluationResult,
        low_ai_insights: CombinedAIInsights,
    ):
        """Low rules (2) + low AI (3) = 0.4*2 + 0.6*3 = 2.6"""
        result = scoring_service.compute_hybrid_score(
            low_rule_result, low_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.final_score == 2.6
    
    def test_weight_breakdown_included(
        self,
        scoring_service: HybridScoringService,
        average_rule_result: EvaluationResult,
        medium_ai_insights: CombinedAIInsights,
    ):
        """Score breakdown should include weights."""
        result = scoring_service.compute_hybrid_score(
            average_rule_result, medium_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.score_breakdown.rules_weight == 0.4
        assert result.score_breakdown.ai_weight == 0.6


# ============================================================================
# Missing Signal Handling Tests
# ============================================================================

class TestMissingSignalHandling:
    """Test weight re-normalization when signals are missing."""
    
    def test_no_ai_insights(
        self,
        scoring_service: HybridScoringService,
        average_rule_result: EvaluationResult,
    ):
        """Without AI, final score equals rule composite."""
        result = scoring_service.compute_hybrid_score(
            average_rule_result, None
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.ai_signal_score == 0.0
        assert result.final_score == result.rule_composite_score
        assert result.score_breakdown.rules_weight == 1.0
        assert result.score_breakdown.ai_weight == 0.0
    
    def test_partial_ai_insights_documentation_only(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
    ):
        """Only documentation signal available."""
        partial_ai = CombinedAIInsights(
            documentation=DocumentationQualityResult(
                clarity="high",
                strengths=[],
                gaps=[],
                suggestions=[],
            ),
            code_clarity=None,
            tech_stack=None,
            recruiter_feedback=None,
            errors=[],
        )
        
        result = scoring_service.compute_hybrid_score(
            perfect_rule_result, partial_ai
        )
        
        assert isinstance(result, HybridScoringResult)
        # Only clarity=high (9) available, so ai_signal_score = 9.0
        assert result.ai_signal_score == 9.0
    
    def test_empty_ai_insights(
        self,
        scoring_service: HybridScoringService,
        average_rule_result: EvaluationResult,
    ):
        """Empty AI insights should use rule-only scoring."""
        empty_ai = CombinedAIInsights(
            documentation=None,
            code_clarity=None,
            tech_stack=None,
            recruiter_feedback=None,
            errors=[],
        )
        
        result = scoring_service.compute_hybrid_score(
            average_rule_result, empty_ai
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.final_score == result.rule_composite_score


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error responses for invalid inputs."""
    
    def test_invalid_score_range(self, scoring_service: HybridScoringService):
        """Score out of 0-10 range should return error."""
        invalid_result = EvaluationResult(
            documentation_score=15,  # Invalid: > 10
            structure_score=5,
            configuration_score=5,
            completeness_score=5,
            issues=[],
        )
        
        result = scoring_service.compute_hybrid_score(invalid_result, None)
        
        assert isinstance(result, HybridScoringError)
        assert result.error.type == "INVALID_RANGE"
        assert "documentation_score" in result.error.message
    
    def test_negative_score(self, scoring_service: HybridScoringService):
        """Negative score should return error."""
        invalid_result = EvaluationResult(
            documentation_score=-1,  # Invalid: < 0
            structure_score=5,
            configuration_score=5,
            completeness_score=5,
            issues=[],
        )
        
        result = scoring_service.compute_hybrid_score(invalid_result, None)
        
        assert isinstance(result, HybridScoringError)
        assert result.error.type == "INVALID_RANGE"


# ============================================================================
# Custom Weight Tests
# ============================================================================

class TestCustomWeights:
    """Test custom weight configurations."""
    
    def test_equal_weights(
        self,
        average_rule_result: EvaluationResult,
        medium_ai_insights: CombinedAIInsights,
    ):
        """50/50 weights: (6.5 + 6) / 2 = 6.25 rounded to 6.2"""
        service = HybridScoringService(rules_weight=0.5, ai_weight=0.5)
        
        result = service.compute_hybrid_score(
            average_rule_result, medium_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        # 0.5 * 6.5 + 0.5 * 6 = 6.25
        assert result.final_score == 6.2  # rounded to 1 decimal
    
    def test_rules_only_weight(
        self,
        average_rule_result: EvaluationResult,
        high_ai_insights: CombinedAIInsights,
    ):
        """100% rules weight ignores AI signals."""
        service = HybridScoringService(rules_weight=1.0, ai_weight=0.0)
        
        result = service.compute_hybrid_score(
            average_rule_result, high_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.final_score == 6.5  # Pure rule composite
    
    def test_ai_only_weight(
        self,
        average_rule_result: EvaluationResult,
        high_ai_insights: CombinedAIInsights,
    ):
        """100% AI weight ignores rule scores."""
        service = HybridScoringService(rules_weight=0.0, ai_weight=1.0)
        
        result = service.compute_hybrid_score(
            average_rule_result, high_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        assert result.final_score == 9.0  # Pure AI signal score
    
    def test_invalid_weight_range(self):
        """Weights outside 0-1 range should raise ValueError."""
        with pytest.raises(ValueError):
            HybridScoringService(rules_weight=1.5, ai_weight=0.5)
        
        with pytest.raises(ValueError):
            HybridScoringService(rules_weight=0.5, ai_weight=-0.1)


# ============================================================================
# QuantifiedSignals Tests
# ============================================================================

class TestQuantifiedSignals:
    """Test the QuantifiedSignals dataclass."""
    
    def test_all_signals_present(self):
        """All three signals available."""
        signals = QuantifiedSignals(
            documentation_clarity=9.0,
            code_organization=6.0,
            naming_consistency=3.0,
        )
        
        assert signals.signal_count == 3
        assert signals.compute_average() == 6.0
    
    def test_partial_signals(self):
        """Only some signals available."""
        signals = QuantifiedSignals(
            documentation_clarity=9.0,
            code_organization=None,
            naming_consistency=3.0,
        )
        
        assert signals.signal_count == 2
        assert signals.compute_average() == 6.0  # (9 + 3) / 2
    
    def test_no_signals(self):
        """No signals available."""
        signals = QuantifiedSignals()
        
        assert signals.signal_count == 0
        assert signals.compute_average() is None
    
    def test_single_signal(self):
        """Only one signal available."""
        signals = QuantifiedSignals(
            documentation_clarity=6.0,
        )
        
        assert signals.signal_count == 1
        assert signals.compute_average() == 6.0


# ============================================================================
# Boundary Tests
# ============================================================================

class TestBoundaryConditions:
    """Test edge cases and boundary conditions."""
    
    def test_minimum_scores(self, scoring_service: HybridScoringService):
        """All minimum scores (0)."""
        rule_result = EvaluationResult(
            documentation_score=0,
            structure_score=0,
            configuration_score=0,
            completeness_score=0,
            issues=[],
        )
        
        result = scoring_service.compute_hybrid_score(rule_result, None)
        
        assert isinstance(result, HybridScoringResult)
        assert result.final_score == 0.0
    
    def test_maximum_scores(
        self,
        scoring_service: HybridScoringService,
        perfect_rule_result: EvaluationResult,
        high_ai_insights: CombinedAIInsights,
    ):
        """Maximum possible hybrid score."""
        result = scoring_service.compute_hybrid_score(
            perfect_rule_result, high_ai_insights
        )
        
        assert isinstance(result, HybridScoringResult)
        # 0.4 * 10 + 0.6 * 9 = 9.4
        assert result.final_score == 9.4
        assert result.final_score <= 10.0
    
    def test_score_rounding(self, scoring_service: HybridScoringService):
        """Scores should be rounded to 1 decimal place."""
        rule_result = EvaluationResult(
            documentation_score=7,
            structure_score=7,
            configuration_score=7,
            completeness_score=7,
            issues=[],
        )
        
        result = scoring_service.compute_hybrid_score(rule_result, None)
        
        assert isinstance(result, HybridScoringResult)
        # Check that all scores have at most 1 decimal place
        assert result.rule_composite_score == 7.0
        assert str(result.final_score).count('.') <= 1
