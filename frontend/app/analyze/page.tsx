'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { RepositoryInput } from '@/components/RepositoryInput';
import { LoadingState } from '@/components/LoadingState';
import { ReportDisplay } from '@/components/ReportDisplay';
import { ErrorDisplay } from '@/components/ErrorDisplay';

/**
 * Application state machine.
 * Each state maps deterministically to UI behavior.
 */
type AppState = 'IDLE' | 'LOADING' | 'SUCCESS' | 'ERROR';

/**
 * Report data structure from backend.
 * Matches Phase 6 frontend payload specification.
 */
interface ReportData {
  status: 'success';
  repo_name: string;
  final_score: number;
  report: {
    summary: string;
    strengths: string[];
    improvements: string[];
    resume_bullets: string[];
  };
  section_scores: {
    documentation: number;
    structure: number;
    configuration: number;
    completeness: number;
  };
}

/**
 * Error data structure from backend.
 */
interface ErrorData {
  type: string;
  message: string;
}

/**
 * Frontend timeout in milliseconds (90 seconds to match backend).
 * Phase 7: Ensures UI doesn't hang indefinitely.
 */
const FRONTEND_TIMEOUT_MS = 90000;

export default function AnalyzePage() {
  const [state, setState] = useState<AppState>('IDLE');
  const [report, setReport] = useState<ReportData | null>(null);
  const [error, setError] = useState<ErrorData | null>(null);

  /**
   * Handle frontend timeout - called by LoadingState when processing takes too long.
   * Phase 7: Provides graceful degradation when backend is slow.
   */
  const handleTimeout = useCallback(() => {
    setState('ERROR');
    setError({
      type: 'TIMEOUT',
      message: 'The analysis is taking longer than expected. Please try again or try a smaller repository.',
    });
  }, []);

  /**
   * Handle repository analysis submission.
   * Prevents duplicate submissions during loading.
   * Phase 7: Includes AbortController for request cancellation.
   */
  const handleAnalyze = async (repoUrl: string) => {
    // Prevent duplicate submissions
    if (state === 'LOADING') return;

    setState('LOADING');
    setError(null);
    setReport(null);

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FRONTEND_TIMEOUT_MS);

    try {
      const response = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo_url: repoUrl }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json();

      if (data.status === 'success') {
        setReport(data);
        setState('SUCCESS');
      } else {
        setError(data.error);
        setState('ERROR');
      }
    } catch (err) {
      clearTimeout(timeoutId);
      
      // Check if it was an abort (timeout)
      if (err instanceof Error && err.name === 'AbortError') {
        setError({
          type: 'TIMEOUT',
          message: 'The analysis is taking longer than expected. Please try again or try a smaller repository.',
        });
      } else {
        // Network or unexpected error
        setError({
          type: 'NETWORK_ERROR',
          message: 'Unable to connect to the server. Please check your connection and try again.',
        });
      }
      setState('ERROR');
    }
  };

  /**
   * Reset to initial state for new analysis.
   */
  const handleReset = () => {
    setState('IDLE');
    setReport(null);
    setError(null);
  };

  return (
    <div className="analyze-page">
      <div className="container-narrow">
        {/* Back Link - Only show when not loading */}
        {state !== 'LOADING' && (
          <div className="analyze-header">
            <Link href="/" className="analyze-back-link">
              <span aria-hidden="true">←</span>
              <span>Back to Home</span>
            </Link>
          </div>
        )}

        {state === 'IDLE' && (
          <RepositoryInput onSubmit={handleAnalyze} />
        )}
        
        {state === 'LOADING' && (
          <LoadingState onTimeout={handleTimeout} timeoutMs={FRONTEND_TIMEOUT_MS} />
        )}
        
        {state === 'SUCCESS' && report && (
          <ReportDisplay report={report} onReset={handleReset} />
        )}
        
        {state === 'ERROR' && error && (
          <ErrorDisplay error={error} onRetry={handleReset} />
        )}
      </div>
    </div>
  );
}
