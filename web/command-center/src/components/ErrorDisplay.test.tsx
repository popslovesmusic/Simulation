import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import {
  ErrorDisplay,
  CompactErrorDisplay,
  ErrorToast,
  useErrorDisplay,
  HelpfulErrorData
} from './ErrorDisplay';

describe('ErrorDisplay', () => {
  const mockError: HelpfulErrorData = {
    error_type: 'ParameterError',
    message: 'num_nodes must be positive',
    context: {
      Parameter: 'num_nodes',
      'Got value': -100,
      Expected: 'positive integer',
    },
    suggestions: [
      'Set num_nodes to a positive value',
      'Try using num_nodes=1024',
    ],
    docs_link: 'docs/user_guide/PARAMETERS.md',
    cause: 'ValueError: Invalid parameter',
  };

  it('should render error message', () => {
    render(<ErrorDisplay error={mockError} />);

    expect(screen.getByText('ParameterError')).toBeInTheDocument();
    expect(screen.getByText('num_nodes must be positive')).toBeInTheDocument();
  });

  it('should render with string error', () => {
    render(<ErrorDisplay error="Something went wrong" />);

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('should render with Error object', () => {
    const error = new Error('Test error');
    render(<ErrorDisplay error={error} />);

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('should show details when expand button clicked', async () => {
    render(<ErrorDisplay error={mockError} />);

    // Initially details are hidden
    expect(screen.queryByText('Context')).not.toBeInTheDocument();

    // Click expand button
    const expandButton = screen.getByLabelText('Show details');
    fireEvent.click(expandButton);

    // Details should now be visible
    await waitFor(() => {
      expect(screen.getByText('Context')).toBeInTheDocument();
    });
  });

  it('should render context information', () => {
    render(<ErrorDisplay error={mockError} />);

    // Expand details
    fireEvent.click(screen.getByLabelText('Show details'));

    // Check context is rendered
    expect(screen.getByText('Parameter:')).toBeInTheDocument();
    expect(screen.getByText('num_nodes')).toBeInTheDocument();
    expect(screen.getByText('Got value:')).toBeInTheDocument();
    expect(screen.getByText('-100')).toBeInTheDocument();
  });

  it('should render suggestions', () => {
    render(<ErrorDisplay error={mockError} />);

    // Expand details
    fireEvent.click(screen.getByLabelText('Show details'));

    // Check suggestions are rendered
    expect(screen.getByText(/Suggested fixes/i)).toBeInTheDocument();
    expect(screen.getByText('Set num_nodes to a positive value')).toBeInTheDocument();
    expect(screen.getByText('Try using num_nodes=1024')).toBeInTheDocument();
  });

  it('should render single suggestion without list', () => {
    const singleSuggestionError: HelpfulErrorData = {
      error_type: 'Error',
      message: 'Test error',
      suggestions: ['Single suggestion'],
    };

    render(<ErrorDisplay error={singleSuggestionError} />);
    fireEvent.click(screen.getByLabelText('Show details'));

    expect(screen.getByText('Suggested fix')).toBeInTheDocument();
    expect(screen.getByText('Single suggestion')).toBeInTheDocument();
  });

  it('should render documentation link', () => {
    render(<ErrorDisplay error={mockError} />);

    // Expand details
    fireEvent.click(screen.getByLabelText('Show details'));

    // Check docs link
    const link = screen.getByText('View documentation');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'docs/user_guide/PARAMETERS.md');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('should render cause information', () => {
    render(<ErrorDisplay error={mockError} />);

    // Expand details
    fireEvent.click(screen.getByLabelText('Show details'));

    // Check cause
    expect(screen.getByText('Caused by')).toBeInTheDocument();
    expect(screen.getByText('ValueError: Invalid parameter')).toBeInTheDocument();
  });

  it('should call onDismiss when dismiss button clicked', () => {
    const onDismiss = vi.fn();
    render(<ErrorDisplay error={mockError} onDismiss={onDismiss} />);

    const dismissButton = screen.getByLabelText('Dismiss error');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it('should toggle details visibility', () => {
    render(<ErrorDisplay error={mockError} />);

    const toggleButton = screen.getByLabelText('Show details');

    // Initially hidden
    expect(screen.queryByText('Context')).not.toBeInTheDocument();

    // Show details
    fireEvent.click(toggleButton);
    expect(screen.getByText('Context')).toBeInTheDocument();

    // Hide details
    fireEvent.click(screen.getByLabelText('Hide details'));
    expect(screen.queryByText('Context')).not.toBeInTheDocument();
  });

  it('should not show expand button when no details available', () => {
    const simpleError: HelpfulErrorData = {
      error_type: 'Error',
      message: 'Simple error with no details',
    };

    render(<ErrorDisplay error={simpleError} />);

    expect(screen.queryByLabelText('Show details')).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <ErrorDisplay error={mockError} className="custom-class" />
    );

    const errorDiv = container.firstChild;
    expect(errorDiv).toHaveClass('custom-class');
  });
});

describe('CompactErrorDisplay', () => {
  it('should render compact error message', () => {
    render(<CompactErrorDisplay message="Error occurred" />);

    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });

  it('should call onDismiss when dismiss button clicked', () => {
    const onDismiss = vi.fn();
    render(<CompactErrorDisplay message="Error" onDismiss={onDismiss} />);

    const dismissButton = screen.getByLabelText('Dismiss');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it('should not show dismiss button when onDismiss not provided', () => {
    render(<CompactErrorDisplay message="Error" />);

    expect(screen.queryByLabelText('Dismiss')).not.toBeInTheDocument();
  });
});

describe('ErrorToast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render toast with error message', () => {
    const onDismiss = vi.fn();
    render(
      <ErrorToast
        error="Toast error"
        onDismiss={onDismiss}
        autoHideDuration={0}
      />
    );

    expect(screen.getByText('Toast error')).toBeInTheDocument();
  });

  it('should auto-dismiss after duration', async () => {
    const onDismiss = vi.fn();
    render(
      <ErrorToast
        error="Auto-hide error"
        onDismiss={onDismiss}
        autoHideDuration={3000}
      />
    );

    expect(onDismiss).not.toHaveBeenCalled();

    // Fast-forward time
    vi.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(onDismiss).toHaveBeenCalledOnce();
    });
  });

  it('should handle Error object', () => {
    const error = new Error('Toast error object');
    const onDismiss = vi.fn();

    render(
      <ErrorToast
        error={error}
        onDismiss={onDismiss}
        autoHideDuration={0}
      />
    );

    expect(screen.getByText('Toast error object')).toBeInTheDocument();
  });

  it('should handle HelpfulErrorData', () => {
    const error: HelpfulErrorData = {
      error_type: 'TestError',
      message: 'Helpful error message',
    };
    const onDismiss = vi.fn();

    render(
      <ErrorToast
        error={error}
        onDismiss={onDismiss}
        autoHideDuration={0}
      />
    );

    expect(screen.getByText('Helpful error message')).toBeInTheDocument();
  });

  it('should allow manual dismissal', () => {
    const onDismiss = vi.fn();
    render(
      <ErrorToast
        error="Manual dismiss"
        onDismiss={onDismiss}
        autoHideDuration={5000}
      />
    );

    const dismissButton = screen.getByLabelText('Dismiss');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalledOnce();
  });
});

describe('useErrorDisplay hook', () => {
  it('should show and clear errors', () => {
    const TestComponent = () => {
      const { error, showError, clearError, ErrorComponent } = useErrorDisplay();

      return (
        <div>
          <button onClick={() => showError('Test error')}>Show Error</button>
          <button onClick={clearError}>Clear Error</button>
          {ErrorComponent}
        </div>
      );
    };

    render(<TestComponent />);

    // Initially no error
    expect(screen.queryByText('Test error')).not.toBeInTheDocument();

    // Show error
    fireEvent.click(screen.getByText('Show Error'));
    expect(screen.getByText('Test error')).toBeInTheDocument();

    // Clear error
    fireEvent.click(screen.getByText('Clear Error'));
    expect(screen.queryByText('Test error')).not.toBeInTheDocument();
  });

  it('should handle HelpfulErrorData', () => {
    const TestComponent = () => {
      const { showError, ErrorComponent } = useErrorDisplay();

      const handleClick = () => {
        showError({
          error_type: 'TestError',
          message: 'Helpful error',
          suggestions: ['Fix suggestion'],
        });
      };

      return (
        <div>
          <button onClick={handleClick}>Show Helpful Error</button>
          {ErrorComponent}
        </div>
      );
    };

    render(<TestComponent />);

    fireEvent.click(screen.getByText('Show Helpful Error'));

    expect(screen.getByText('TestError')).toBeInTheDocument();
    expect(screen.getByText('Helpful error')).toBeInTheDocument();
  });

  it('should handle Error object', () => {
    const TestComponent = () => {
      const { showError, ErrorComponent } = useErrorDisplay();

      const handleClick = () => {
        showError(new Error('Error object'));
      };

      return (
        <div>
          <button onClick={handleClick}>Show Error Object</button>
          {ErrorComponent}
        </div>
      );
    };

    render(<TestComponent />);

    fireEvent.click(screen.getByText('Show Error Object'));

    expect(screen.getByText('Error object')).toBeInTheDocument();
  });
});
