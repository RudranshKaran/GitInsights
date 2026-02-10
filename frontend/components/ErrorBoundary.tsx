'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary Component
 * 
 * Phase 7: Catches React rendering errors and prevents white screen of death.
 * Provides a calm, professional fallback UI when components crash.
 * Never exposes stack traces or technical details to users.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error for debugging (could send to error tracking service)
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <section className="error-section" role="alert" aria-live="assertive">
          <div className="error-icon" aria-hidden="true">⚠️</div>
          <h2 className="error-title">Something went wrong</h2>
          <p className="error-message">
            We encountered an unexpected issue. Please refresh the page to try again.
          </p>
          <button onClick={this.handleReset} className="btn btn-primary">
            Try Again
          </button>
        </section>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
