interface ErrorData {
  type: string;
  message: string;
}

interface Props {
  error: ErrorData;
  onRetry: () => void;
}

/**
 * Error Display Component
 * 
 * Shows friendly, human-readable error messages.
 * Provides clear next action for the user.
 * Never shows stack traces or internal error codes.
 */
export function ErrorDisplay({ error, onRetry }: Props) {
  return (
    <section className="error-section" role="alert" aria-live="assertive">
      <div className="error-icon" aria-hidden="true">⚠️</div>
      <h2 className="error-title">Something went wrong</h2>
      <p className="error-message">{error.message}</p>
      <button onClick={onRetry} className="btn btn-primary btn-lg">
        Try Again
      </button>
    </section>
  );
}
