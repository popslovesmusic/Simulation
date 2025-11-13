import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  ProgressBar,
  ProgressSpinner,
  ProgressRing,
  StepProgress,
  ProgressCard,
} from './ProgressIndicator';

describe('ProgressBar', () => {
  it('should render with correct percentage', () => {
    render(<ProgressBar value={50} />);

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '50');
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('should render with label', () => {
    render(<ProgressBar value={75} label="Processing" />);

    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('should hide percentage when showPercentage is false', () => {
    render(<ProgressBar value={50} showPercentage={false} />);

    expect(screen.queryByText('50%')).not.toBeInTheDocument();
  });

  it('should clamp value to 0-100 range', () => {
    const { rerender } = render(<ProgressBar value={150} />);

    let progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '100');

    rerender(<ProgressBar value={-50} />);
    progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');
  });

  it('should apply different sizes', () => {
    const { container, rerender } = render(<ProgressBar value={50} size="sm" />);

    let bar = container.querySelector('.h-1');
    expect(bar).toBeInTheDocument();

    rerender(<ProgressBar value={50} size="md" />);
    bar = container.querySelector('.h-2');
    expect(bar).toBeInTheDocument();

    rerender(<ProgressBar value={50} size="lg" />);
    bar = container.querySelector('.h-3');
    expect(bar).toBeInTheDocument();
  });

  it('should apply different colors', () => {
    const { container, rerender } = render(<ProgressBar value={50} color="blue" />);

    let bar = container.querySelector('.bg-blue-600');
    expect(bar).toBeInTheDocument();

    rerender(<ProgressBar value={50} color="green" />);
    bar = container.querySelector('.bg-green-600');
    expect(bar).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(<ProgressBar value={50} className="custom-class" />);

    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-class');
  });
});

describe('ProgressSpinner', () => {
  it('should render spinner', () => {
    const { container } = render(<ProgressSpinner />);

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should render with label', () => {
    render(<ProgressSpinner label="Loading..." />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should apply different sizes', () => {
    const { container, rerender } = render(<ProgressSpinner size="sm" />);

    let spinner = container.querySelector('.w-4');
    expect(spinner).toBeInTheDocument();

    rerender(<ProgressSpinner size="md" />);
    spinner = container.querySelector('.w-6');
    expect(spinner).toBeInTheDocument();

    rerender(<ProgressSpinner size="lg" />);
    spinner = container.querySelector('.w-8');
    expect(spinner).toBeInTheDocument();
  });
});

describe('ProgressRing', () => {
  it('should render SVG ring', () => {
    const { container } = render(<ProgressRing value={50} />);

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();

    const circles = container.querySelectorAll('circle');
    expect(circles).toHaveLength(2); // Background + progress
  });

  it('should display percentage in center', () => {
    render(<ProgressRing value={75} />);

    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('should hide percentage when showPercentage is false', () => {
    render(<ProgressRing value={50} showPercentage={false} />);

    expect(screen.queryByText('50%')).not.toBeInTheDocument();
  });

  it('should render with label', () => {
    render(<ProgressRing value={50} label="Progress" />);

    expect(screen.getByText('Progress')).toBeInTheDocument();
  });

  it('should clamp value to 0-100', () => {
    const { container, rerender } = render(<ProgressRing value={150} />);

    expect(screen.getByText('100%')).toBeInTheDocument();

    rerender(<ProgressRing value={-50} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('should apply custom size', () => {
    const { container } = render(<ProgressRing value={50} size={200} />);

    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '200');
    expect(svg).toHaveAttribute('height', '200');
  });
});

describe('StepProgress', () => {
  const steps = [
    { id: '1', label: 'Step 1', status: 'completed' as const },
    { id: '2', label: 'Step 2', status: 'active' as const },
    { id: '3', label: 'Step 3', status: 'pending' as const },
    { id: '4', label: 'Step 4', status: 'error' as const },
  ];

  it('should render all steps', () => {
    render(<StepProgress steps={steps} />);

    expect(screen.getByText('Step 1')).toBeInTheDocument();
    expect(screen.getByText('Step 2')).toBeInTheDocument();
    expect(screen.getByText('Step 3')).toBeInTheDocument();
    expect(screen.getByText('Step 4')).toBeInTheDocument();
  });

  it('should render horizontal orientation by default', () => {
    const { container } = render(<StepProgress steps={steps} />);

    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('flex', 'items-center');
  });

  it('should render vertical orientation', () => {
    const { container } = render(
      <StepProgress steps={steps} orientation="vertical" />
    );

    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('flex', 'flex-col');
  });

  it('should show correct icons for each status', () => {
    const { container } = render(<StepProgress steps={steps} />);

    // Completed: CheckCircle2
    // Active: Loader2 (spinning)
    // Pending: Clock
    // Error: XCircle

    const spinners = container.querySelectorAll('.animate-spin');
    expect(spinners.length).toBeGreaterThan(0);
  });

  it('should render connectors between steps', () => {
    const { container } = render(<StepProgress steps={steps} />);

    // Should have N-1 connectors for N steps
    const connectors = container.querySelectorAll('.flex-1.mx-2');
    expect(connectors).toHaveLength(steps.length - 1);
  });
});

describe('ProgressCard', () => {
  it('should render title and progress', () => {
    render(<ProgressCard title="Processing" progress={50} />);

    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('should render description', () => {
    render(
      <ProgressCard
        title="Processing"
        progress={50}
        description="Step 1 of 3"
      />
    );

    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument();
  });

  it('should format time remaining correctly', () => {
    const { rerender } = render(
      <ProgressCard
        title="Processing"
        progress={50}
        estimatedTimeRemaining={45}
      />
    );

    expect(screen.getByText(/45s/)).toBeInTheDocument();

    rerender(
      <ProgressCard
        title="Processing"
        progress={50}
        estimatedTimeRemaining={125}
      />
    );

    expect(screen.getByText(/2m 5s/)).toBeInTheDocument();

    rerender(
      <ProgressCard
        title="Processing"
        progress={50}
        estimatedTimeRemaining={3725}
      />
    );

    expect(screen.getByText(/1h 2m/)).toBeInTheDocument();
  });

  it('should call onCancel when cancel button clicked', () => {
    const onCancel = vi.fn();
    render(
      <ProgressCard
        title="Processing"
        progress={50}
        onCancel={onCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('should not show cancel button when onCancel not provided', () => {
    render(<ProgressCard title="Processing" progress={50} />);

    expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <ProgressCard
        title="Processing"
        progress={50}
        className="custom-class"
      />
    );

    const card = container.firstChild;
    expect(card).toHaveClass('custom-class');
  });
});

describe('Progress components accessibility', () => {
  it('ProgressBar should have proper ARIA attributes', () => {
    render(<ProgressBar value={60} label="Test" />);

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '60');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('should handle keyboard navigation for cancel button', () => {
    const onCancel = vi.fn();
    render(
      <ProgressCard
        title="Processing"
        progress={50}
        onCancel={onCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');

    // Simulate keyboard interaction
    cancelButton.focus();
    expect(document.activeElement).toBe(cancelButton);

    fireEvent.click(cancelButton);
    expect(onCancel).toHaveBeenCalled();
  });
});

describe('Progress components edge cases', () => {
  it('should handle progress value of 0', () => {
    render(<ProgressBar value={0} />);

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('should handle progress value of 100', () => {
    render(<ProgressBar value={100} />);

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '100');
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('should handle empty steps array', () => {
    const { container } = render(<StepProgress steps={[]} />);

    expect(container.firstChild).toBeInTheDocument();
    // Should render without errors
  });

  it('should handle single step', () => {
    const singleStep = [
      { id: '1', label: 'Only Step', status: 'completed' as const },
    ];

    render(<StepProgress steps={singleStep} />);

    expect(screen.getByText('Only Step')).toBeInTheDocument();

    // Should have no connectors
    const { container } = render(<StepProgress steps={singleStep} />);
    const connectors = container.querySelectorAll('.flex-1.mx-2');
    expect(connectors).toHaveLength(0);
  });
});
