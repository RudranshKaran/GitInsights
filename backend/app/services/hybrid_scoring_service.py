"""
Hybrid Scoring Service (Phase 4)

Combines deterministic rule-based scores with quantified AI signals
to produce stable, explainable numeric scores.

This service follows strict determinism guarantees:
- Same input → Same output
- No randomness or probabilistic logic
- All scoring logic is explicitly defined and traceable
- No external service calls or AI generation
"""

from dataclasses import dataclass
from typing import Literal

from app.services.evaluation_service import EvaluationResult
from app.schemas.models import (
    CombinedAIInsights,
    HybridScoringResult,
    HybridScoreBreakdown,
    HybridScoringError,
    HybridScoringErrorDetail,
)


# ============================================================================
# Fixed Mapping Tables (Deterministic)
# ============================================================================

# Documentation clarity: low | medium | high → numeric
CLARITY_MAPPING: dict[str, float] = {
    "low": 3.0,
    "medium": 6.0,
    "high": 9.0,
}

# Code organization: poor | acceptable | well-structured → numeric
ORGANIZATION_MAPPING: dict[str, float] = {
    "poor": 3.0,
    "acceptable": 6.0,
    "well-structured": 9.0,
}

# Naming consistency: low | medium | high → numeric
NAMING_MAPPING: dict[str, float] = {
    "low": 3.0,
    "medium": 6.0,
    "high": 9.0,
}

# Weight configuration
DEFAULT_RULES_WEIGHT = 0.4
DEFAULT_AI_WEIGHT = 0.6


@dataclass
class QuantifiedSignals:
    """
    Intermediate container for quantified AI signals.
    
    Holds the numeric values after applying fixed mappings.
    Tracks which signals were successfully quantified.
    """
    
    documentation_clarity: float | None = None
    code_organization: float | None = None
    naming_consistency: float | None = None
    
    @property
    def available_signals(self) -> list[float]:
        """Return list of non-None signal values."""
        signals = [
            self.documentation_clarity,
            self.code_organization,
            self.naming_consistency,
        ]
        return [s for s in signals if s is not None]
    
    @property
    def signal_count(self) -> int:
        """Number of successfully quantified signals."""
        return len(self.available_signals)
    
    def compute_average(self) -> float | None:
        """
        Compute average of available signals.
        
        Returns None if no signals are available.
        Re-normalizes automatically based on available signals.
        """
        signals = self.available_signals
        if not signals:
            return None
        return sum(signals) / len(signals)


class HybridScoringService:
    """
    Hybrid Scoring Engine for combining rule-based and AI-derived scores.
    
    Responsibilities:
    1. Compute rule-based composite score (average of 4 dimensions)
    2. Quantify AI signals using fixed mapping tables
    3. Combine with configurable weights (default: 40% rules, 60% AI)
    4. Handle missing signals with weight re-normalization
    
    Guarantees:
    - Deterministic: Same input always produces same output
    - Explainable: All scoring decisions are traceable
    - Bounded: All scores are within 0-10 range
    """
    
    def __init__(
        self,
        rules_weight: float = DEFAULT_RULES_WEIGHT,
        ai_weight: float = DEFAULT_AI_WEIGHT,
    ):
        """
        Initialize the scoring engine with configurable weights.
        
        Args:
            rules_weight: Weight for rule-based composite (default: 0.4)
            ai_weight: Weight for AI signal score (default: 0.6)
        """
        if not (0.0 <= rules_weight <= 1.0):
            raise ValueError("rules_weight must be between 0.0 and 1.0")
        if not (0.0 <= ai_weight <= 1.0):
            raise ValueError("ai_weight must be between 0.0 and 1.0")
        
        self.rules_weight = rules_weight
        self.ai_weight = ai_weight
    
    def compute_hybrid_score(
        self,
        rule_result: EvaluationResult,
        ai_insights: CombinedAIInsights | None,
    ) -> HybridScoringResult | HybridScoringError:
        """
        Compute the final hybrid score.
        
        Combines rule-based scores with quantified AI signals.
        
        Args:
            rule_result: EvaluationResult from Phase 2
            ai_insights: CombinedAIInsights from Phase 3 (can be None)
            
        Returns:
            HybridScoringResult on success, HybridScoringError on failure
        """
        # Validate rule-based scores (required)
        validation_error = self._validate_rule_scores(rule_result)
        if validation_error:
            return validation_error
        
        # Step 1: Compute rule-based composite
        rule_composite = self._compute_rule_composite(rule_result)
        
        # Step 2: Quantify AI signals
        quantified = self._quantify_ai_signals(ai_insights)
        ai_signal_score = quantified.compute_average()
        
        # Step 3: Compute final score with weight handling
        final_score, breakdown = self._compute_final_score(
            rule_composite=rule_composite,
            ai_signal_score=ai_signal_score,
        )
        
        return HybridScoringResult(
            rule_composite_score=round(rule_composite, 1),
            ai_signal_score=round(ai_signal_score, 1) if ai_signal_score is not None else 0.0,
            final_score=round(final_score, 1),
            score_breakdown=breakdown,
        )
    
    def _validate_rule_scores(
        self,
        rule_result: EvaluationResult,
    ) -> HybridScoringError | None:
        """
        Validate that all required rule-based scores are present and in range.
        
        Returns HybridScoringError if validation fails, None otherwise.
        """
        required_scores = [
            ("documentation_score", rule_result.documentation_score),
            ("structure_score", rule_result.structure_score),
            ("configuration_score", rule_result.configuration_score),
            ("completeness_score", rule_result.completeness_score),
        ]
        
        for name, value in required_scores:
            if value is None:
                return HybridScoringError(
                    error=HybridScoringErrorDetail(
                        type="MISSING_INPUT",
                        message=f"Missing required rule score: {name}",
                    )
                )
            if not (0 <= value <= 10):
                return HybridScoringError(
                    error=HybridScoringErrorDetail(
                        type="INVALID_RANGE",
                        message=f"Score {name} out of range: {value} (expected 0-10)",
                    )
                )
        
        return None
    
    def _compute_rule_composite(self, rule_result: EvaluationResult) -> float:
        """
        Compute the rule-based composite score.
        
        Simple average of the four dimension scores.
        
        Formula:
            rule_composite = average(
                documentation_score,
                structure_score,
                configuration_score,
                completeness_score
            )
        """
        scores = [
            rule_result.documentation_score,
            rule_result.structure_score,
            rule_result.configuration_score,
            rule_result.completeness_score,
        ]
        return sum(scores) / len(scores)
    
    def _quantify_ai_signals(
        self,
        ai_insights: CombinedAIInsights | None,
    ) -> QuantifiedSignals:
        """
        Convert qualitative AI signals to numeric values using fixed mappings.
        
        Mapping tables:
        - Documentation clarity: low→3, medium→6, high→9
        - Code organization: poor→3, acceptable→6, well-structured→9
        - Naming consistency: low→3, medium→6, high→9
        
        Missing or invalid signals are set to None (excluded from average).
        """
        signals = QuantifiedSignals()
        
        if ai_insights is None:
            return signals
        
        # Documentation clarity
        if ai_insights.documentation and ai_insights.documentation.clarity:
            clarity = ai_insights.documentation.clarity
            if clarity in CLARITY_MAPPING:
                signals.documentation_clarity = CLARITY_MAPPING[clarity]
        
        # Code organization
        if ai_insights.code_clarity and ai_insights.code_clarity.organization:
            organization = ai_insights.code_clarity.organization
            if organization in ORGANIZATION_MAPPING:
                signals.code_organization = ORGANIZATION_MAPPING[organization]
        
        # Naming consistency
        if ai_insights.code_clarity and ai_insights.code_clarity.naming_consistency:
            naming = ai_insights.code_clarity.naming_consistency
            if naming in NAMING_MAPPING:
                signals.naming_consistency = NAMING_MAPPING[naming]
        
        return signals
    
    def _compute_final_score(
        self,
        rule_composite: float,
        ai_signal_score: float | None,
    ) -> tuple[float, HybridScoreBreakdown]:
        """
        Compute the final weighted hybrid score.
        
        Default formula:
            final_score = 0.4 * rule_composite + 0.6 * ai_signal_score
        
        If AI signals are missing, re-normalize weights:
            final_score = rule_composite (100% rules weight)
        
        Returns:
            Tuple of (final_score, breakdown)
        """
        if ai_signal_score is None:
            # No AI signals available - use only rule-based score
            return rule_composite, HybridScoreBreakdown(
                rules_weight=1.0,
                ai_weight=0.0,
            )
        
        # Standard weighted combination
        final_score = (
            self.rules_weight * rule_composite +
            self.ai_weight * ai_signal_score
        )
        
        # Ensure bounds
        final_score = max(0.0, min(10.0, final_score))
        
        return final_score, HybridScoreBreakdown(
            rules_weight=self.rules_weight,
            ai_weight=self.ai_weight,
        )
