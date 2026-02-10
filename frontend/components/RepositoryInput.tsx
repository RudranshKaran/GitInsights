'use client';

import { useState, FormEvent } from 'react';

interface Props {
  onSubmit: (url: string) => void;
}

/**
 * GitHub URL validation pattern.
 * Matches: https://github.com/owner/repo
 * Allows trailing slash, .git suffix, and branch paths.
 */
const GITHUB_URL_PATTERN = /^https?:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+/;

/**
 * Repository Input Component
 * 
 * Handles GitHub URL input with client-side validation.
 * Provides immediate feedback for invalid input.
 */
export function RepositoryInput({ onSubmit }: Props) {
  const [url, setUrl] = useState('');
  const [validationError, setValidationError] = useState('');
  const [touched, setTouched] = useState(false);

  /**
   * Validate GitHub URL format on client side.
   */
  const validateUrl = (input: string): boolean => {
    if (!input.trim()) {
      return false;
    }
    return GITHUB_URL_PATTERN.test(input.trim());
  };

  /**
   * Handle input change with validation.
   */
  const handleChange = (value: string) => {
    setUrl(value);
    
    if (touched) {
      if (!value.trim()) {
        setValidationError('Please enter a GitHub repository URL');
      } else if (!validateUrl(value)) {
        setValidationError('Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)');
      } else {
        setValidationError('');
      }
    }
  };

  /**
   * Handle input blur for validation.
   */
  const handleBlur = () => {
    setTouched(true);
    if (!url.trim()) {
      setValidationError('Please enter a GitHub repository URL');
    } else if (!validateUrl(url)) {
      setValidationError('Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)');
    }
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setTouched(true);

    if (!url.trim()) {
      setValidationError('Please enter a GitHub repository URL');
      return;
    }

    if (!validateUrl(url)) {
      setValidationError('Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)');
      return;
    }

    setValidationError('');
    onSubmit(url.trim());
  };

  return (
    <section className="hero">
      <h1 className="hero-title-gradient">GitInsight</h1>
      <p className="hero-subtitle">
        Evaluate your GitHub projects for internship readiness. 
        Get actionable feedback and resume-ready bullet points.
      </p>

      <div className="input-section">
        <form onSubmit={handleSubmit} className="input-group" noValidate>
          <div>
            <label htmlFor="repo-url" className="sr-only">
              GitHub Repository URL
            </label>
            <input
              id="repo-url"
              type="url"
              className={`input input-lg ${validationError ? 'input-error' : ''}`}
              value={url}
              onChange={(e) => handleChange(e.target.value)}
              onBlur={handleBlur}
              placeholder="https://github.com/username/repository"
              aria-describedby={validationError ? 'url-error' : 'url-hint'}
              aria-invalid={!!validationError}
              autoComplete="url"
              autoFocus
            />
            {validationError && (
              <p id="url-error" className="validation-error" role="alert">
                {validationError}
              </p>
            )}
            {!validationError && (
              <p id="url-hint" className="input-hint">
                Enter a public GitHub repository URL to analyze
              </p>
            )}
          </div>

          <button type="submit" className="btn btn-primary btn-lg">
            Analyze Repository
          </button>
        </form>
      </div>
    </section>
  );
}
