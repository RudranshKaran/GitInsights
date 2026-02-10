"""
Pipelines Module

Contains evaluation pipeline orchestration logic
for sequential repository analysis steps.

Main Components:
- AnalysisPipeline: Full analysis orchestrator (Phase 1 + 2 + 3)
- PipelineError: Structured error for pipeline failures
"""

from app.pipelines.analysis_pipeline import AnalysisPipeline, PipelineError

__all__ = ["AnalysisPipeline", "PipelineError"]
