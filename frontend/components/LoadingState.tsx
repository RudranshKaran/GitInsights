/**
 * Loading State Component
 * 
 * Phase 7: Enhanced loading indicator with progress messaging and timeout awareness.
 * Displays clear progress in simple, non-technical terms.
 * No internal phase names are exposed to users.
 * Provides reassurance during longer processing times.
 */

'use client';

import { useState, useEffect } from 'react';

/**
 * Progress messages shown at different time intervals.
 * Designed to keep users informed without exposing internal processes.
 */
const PROGRESS_MESSAGES = [
  { delay: 0, message: 'Analyzing repository...', subtext: 'This may take a moment' },
  { delay: 5000, message: 'Fetching repository data...', subtext: 'Reading files and structure' },
  { delay: 15000, message: 'Evaluating code quality...', subtext: 'Almost there' },
  { delay: 30000, message: 'Generating your report...', subtext: 'Just a bit longer' },
  { delay: 60000, message: 'Still working on it...', subtext: 'Large repositories take more time' },
];

interface LoadingStateProps {
  /** Optional callback when loading times out (for parent component awareness) */
  onTimeout?: () => void;
  /** Timeout duration in milliseconds (default: 90000ms / 90s) */
  timeoutMs?: number;
}

export function LoadingState({ onTimeout, timeoutMs = 90000 }: LoadingStateProps) {
  const [currentMessage, setCurrentMessage] = useState(PROGRESS_MESSAGES[0]);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    // Update elapsed time every second
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1000);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Update message based on elapsed time
    const applicableMessages = PROGRESS_MESSAGES.filter(
      (msg) => msg.delay <= elapsedTime
    );
    if (applicableMessages.length > 0) {
      setCurrentMessage(applicableMessages[applicableMessages.length - 1]);
    }
  }, [elapsedTime]);

  useEffect(() => {
    // Handle timeout
    if (elapsedTime >= timeoutMs && onTimeout) {
      onTimeout();
    }
  }, [elapsedTime, timeoutMs, onTimeout]);

  return (
    <section className="loading-section" aria-busy="true" aria-live="polite">
      <div className="spinner" role="status" aria-label="Analyzing repository" />
      <p className="loading-text">{currentMessage.message}</p>
      <p className="loading-subtext">{currentMessage.subtext}</p>
    </section>
  );
}

