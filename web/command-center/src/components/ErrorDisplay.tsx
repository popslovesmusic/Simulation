/**
 * ErrorDisplay Component
 *
 * Displays helpful error messages with context, suggestions, and actions.
 * Corresponds to the backend HelpfulError exception system.
 */

import React from 'react';
import { AlertTriangle, Info, BookOpen, X, ChevronDown, ChevronUp } from 'lucide-react';

export interface HelpfulErrorData {
  error_type: string;
  message: string;
  context?: Record<string, any>;
  suggestions?: string[];
  docs_link?: string;
  cause?: string;
}

interface ErrorDisplayProps {
  error: HelpfulErrorData | Error | string;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onDismiss,
  className = ''
}) => {
  const [showDetails, setShowDetails] = React.useState(false);

  // Normalize error to HelpfulErrorData format
  const errorData: HelpfulErrorData = React.useMemo(() => {
    if (typeof error === 'string') {
      return {
        error_type: 'Error',
        message: error,
      };
    } else if (error instanceof Error) {
      return {
        error_type: error.name,
        message: error.message,
      };
    } else {
      return error;
    }
  }, [error]);

  const hasContext = errorData.context && Object.keys(errorData.context).length > 0;
  const hasSuggestions = errorData.suggestions && errorData.suggestions.length > 0;
  const hasCause = !!errorData.cause;
  const hasDetails = hasContext || hasSuggestions || hasCause || errorData.docs_link;

  return (
    <div
      className={`bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg shadow-md ${className}`}
      role="alert"
      aria-live="assertive"
    >
      {/* Header */}
      <div className="flex items-start gap-3 p-4">
        <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-red-900 dark:text-red-100">
            {errorData.error_type}
          </h3>
          <p className="mt-1 text-sm text-red-800 dark:text-red-200">
            {errorData.message}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {hasDetails && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-1 hover:bg-red-100 dark:hover:bg-red-800/30 rounded transition-colors"
              aria-label={showDetails ? 'Hide details' : 'Show details'}
              aria-expanded={showDetails}
            >
              {showDetails ? (
                <ChevronUp className="w-4 h-4 text-red-700 dark:text-red-300" />
              ) : (
                <ChevronDown className="w-4 h-4 text-red-700 dark:text-red-300" />
              )}
            </button>
          )}

          {onDismiss && (
            <button
              onClick={onDismiss}
              className="p-1 hover:bg-red-100 dark:hover:bg-red-800/30 rounded transition-colors"
              aria-label="Dismiss error"
            >
              <X className="w-4 h-4 text-red-700 dark:text-red-300" />
            </button>
          )}
        </div>
      </div>

      {/* Details (collapsible) */}
      {showDetails && hasDetails && (
        <div className="border-t border-red-200 dark:border-red-800 px-4 py-3 space-y-3">
          {/* Context */}
          {hasContext && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Info className="w-4 h-4 text-red-600 dark:text-red-400" />
                <h4 className="text-sm font-medium text-red-900 dark:text-red-100">
                  Context
                </h4>
              </div>
              <dl className="space-y-1 text-sm">
                {Object.entries(errorData.context!).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <dt className="font-medium text-red-800 dark:text-red-200 min-w-[120px]">
                      {key}:
                    </dt>
                    <dd className="text-red-700 dark:text-red-300 font-mono text-xs break-all">
                      {String(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Suggestions */}
          {hasSuggestions && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Info className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h4 className="text-sm font-medium text-red-900 dark:text-red-100">
                  Suggested fix{errorData.suggestions!.length > 1 ? 'es' : ''}
                </h4>
              </div>
              {errorData.suggestions!.length === 1 ? (
                <p className="text-sm text-red-800 dark:text-red-200 pl-6">
                  {errorData.suggestions![0]}
                </p>
              ) : (
                <ol className="list-decimal list-inside space-y-1 text-sm text-red-800 dark:text-red-200 pl-6">
                  {errorData.suggestions!.map((suggestion, idx) => (
                    <li key={idx}>{suggestion}</li>
                  ))}
                </ol>
              )}
            </div>
          )}

          {/* Documentation Link */}
          {errorData.docs_link && (
            <div>
              <a
                href={errorData.docs_link}
                className="inline-flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                <BookOpen className="w-4 h-4" />
                View documentation
              </a>
            </div>
          )}

          {/* Cause */}
          {hasCause && (
            <div>
              <h4 className="text-sm font-medium text-red-900 dark:text-red-100 mb-1">
                Caused by
              </h4>
              <p className="text-sm text-red-700 dark:text-red-300 font-mono bg-red-100 dark:bg-red-900/30 p-2 rounded">
                {errorData.cause}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ErrorBoundary with ErrorDisplay
 *
 * Catches React errors and displays them using ErrorDisplay component.
 */
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="p-4">
          <ErrorDisplay
            error={this.state.error}
            onDismiss={() => this.setState({ hasError: false, error: null })}
          />
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook for displaying errors
 */
export const useErrorDisplay = () => {
  const [error, setError] = React.useState<HelpfulErrorData | Error | string | null>(null);

  const showError = React.useCallback((err: HelpfulErrorData | Error | string) => {
    setError(err);
  }, []);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  const ErrorComponent = React.useMemo(() => {
    if (!error) return null;
    return <ErrorDisplay error={error} onDismiss={clearError} />;
  }, [error, clearError]);

  return {
    error,
    showError,
    clearError,
    ErrorComponent,
  };
};

/**
 * Compact error display for inline use
 */
interface CompactErrorDisplayProps {
  message: string;
  onDismiss?: () => void;
}

export const CompactErrorDisplay: React.FC<CompactErrorDisplayProps> = ({
  message,
  onDismiss
}) => {
  return (
    <div
      className="flex items-center gap-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm"
      role="alert"
    >
      <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
      <span className="flex-1 text-red-800 dark:text-red-200">{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="p-0.5 hover:bg-red-100 dark:hover:bg-red-800/30 rounded transition-colors"
          aria-label="Dismiss"
        >
          <X className="w-3.5 h-3.5 text-red-700 dark:text-red-300" />
        </button>
      )}
    </div>
  );
};

/**
 * Toast-style error notification
 */
interface ErrorToastProps {
  error: HelpfulErrorData | Error | string;
  onDismiss: () => void;
  autoHideDuration?: number;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({
  error,
  onDismiss,
  autoHideDuration = 5000
}) => {
  React.useEffect(() => {
    if (autoHideDuration > 0) {
      const timer = setTimeout(onDismiss, autoHideDuration);
      return () => clearTimeout(timer);
    }
  }, [autoHideDuration, onDismiss]);

  const message = typeof error === 'string'
    ? error
    : error instanceof Error
    ? error.message
    : error.message;

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md animate-slide-up">
      <CompactErrorDisplay message={message} onDismiss={onDismiss} />
    </div>
  );
};

// Example usage
export const ErrorDisplayExample: React.FC = () => {
  const { showError, ErrorComponent } = useErrorDisplay();

  const handleParameterError = () => {
    showError({
      error_type: 'ParameterError',
      message: 'num_nodes must be positive',
      context: {
        Parameter: 'num_nodes',
        'Got value': -100,
        Expected: 'positive integer',
        'Valid range': '1 to 1,000,000',
      },
      suggestions: [
        'Try using num_nodes=1024 or num_nodes=4096',
        'Check the parameter constraints in the documentation',
      ],
      docs_link: 'docs/user_guide/PARAMETERS.md',
    });
  };

  const handleFileError = () => {
    showError({
      error_type: 'FileError',
      message: 'Could not read mission file',
      context: {
        'File path': '/path/to/mission.json',
        Operation: 'read',
      },
      suggestions: [
        'Check that the file exists: /path/to/mission.json',
        'Verify you have read permissions',
      ],
      docs_link: 'docs/user_guide/FILE_OPERATIONS.md',
      cause: 'FileNotFoundError: No such file',
    });
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">Error Display Examples</h2>

      <div className="space-x-2">
        <button
          onClick={handleParameterError}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Show Parameter Error
        </button>
        <button
          onClick={handleFileError}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Show File Error
        </button>
      </div>

      {ErrorComponent}
    </div>
  );
};
