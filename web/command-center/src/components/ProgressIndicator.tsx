/**
 * Progress Indicator Components
 *
 * Provides various progress indicators for long-running operations:
 * - ProgressBar: Determinate progress bar with percentage
 * - ProgressSpinner: Indeterminate spinner for unknown duration
 * - ProgressRing: Circular progress indicator
 * - StepProgress: Multi-step progress indicator
 */

import React from 'react';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';

/**
 * Linear progress bar with percentage
 */
interface ProgressBarProps {
  value: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'green' | 'yellow' | 'red';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercentage = true,
  size = 'md',
  color = 'blue',
  className = ''
}) => {
  const clampedValue = Math.min(Math.max(value, 0), 100);

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const colorClasses = {
    blue: 'bg-blue-600 dark:bg-blue-500',
    green: 'bg-green-600 dark:bg-green-500',
    yellow: 'bg-yellow-600 dark:bg-yellow-500',
    red: 'bg-red-600 dark:bg-red-500',
  };

  return (
    <div className={className}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {label}
            </span>
          )}
          {showPercentage && (
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {clampedValue.toFixed(0)}%
            </span>
          )}
        </div>
      )}

      <div
        className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden ${sizeClasses[size]}`}
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={`${sizeClasses[size]} ${colorClasses[color]} transition-all duration-300 ease-out rounded-full`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};

/**
 * Indeterminate spinner for unknown duration operations
 */
interface ProgressSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ProgressSpinner: React.FC<ProgressSpinnerProps> = ({
  label,
  size = 'md',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <Loader2 className={`${sizeClasses[size]} text-blue-600 dark:text-blue-400 animate-spin`} />
      {label && (
        <span className="text-sm text-gray-700 dark:text-gray-300">
          {label}
        </span>
      )}
    </div>
  );
};

/**
 * Circular progress ring
 */
interface ProgressRingProps {
  value: number; // 0-100
  size?: number;
  strokeWidth?: number;
  color?: 'blue' | 'green' | 'yellow' | 'red';
  label?: string;
  showPercentage?: boolean;
  className?: string;
}

export const ProgressRing: React.FC<ProgressRingProps> = ({
  value,
  size = 120,
  strokeWidth = 8,
  color = 'blue',
  label,
  showPercentage = true,
  className = ''
}) => {
  const clampedValue = Math.min(Math.max(value, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedValue / 100) * circumference;

  const colorClasses = {
    blue: 'stroke-blue-600 dark:stroke-blue-400',
    green: 'stroke-green-600 dark:stroke-green-400',
    yellow: 'stroke-yellow-600 dark:stroke-yellow-400',
    red: 'stroke-red-600 dark:stroke-red-400',
  };

  return (
    <div className={`inline-flex flex-col items-center ${className}`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className="stroke-gray-200 dark:stroke-gray-700"
            strokeWidth={strokeWidth}
            fill="none"
          />

          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className={`${colorClasses[color]} transition-all duration-300 ease-out`}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>

        {/* Center label */}
        {showPercentage && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-semibold text-gray-800 dark:text-gray-200">
              {clampedValue.toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {label && (
        <span className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          {label}
        </span>
      )}
    </div>
  );
};

/**
 * Multi-step progress indicator
 */
interface Step {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}

interface StepProgressProps {
  steps: Step[];
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

export const StepProgress: React.FC<StepProgressProps> = ({
  steps,
  orientation = 'horizontal',
  className = ''
}) => {
  const getStepIcon = (status: Step['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'active':
        return <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-gray-400 dark:text-gray-600" />;
    }
  };

  const getStepColor = (status: Step['status']) => {
    switch (status) {
      case 'completed':
        return 'border-green-600 dark:border-green-400 bg-green-50 dark:bg-green-900/20';
      case 'error':
        return 'border-red-600 dark:border-red-400 bg-red-50 dark:bg-red-900/20';
      case 'active':
        return 'border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20';
      case 'pending':
        return 'border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800';
    }
  };

  const getConnectorColor = (fromStatus: Step['status'], toStatus: Step['status']) => {
    if (fromStatus === 'completed') {
      return 'bg-green-600 dark:bg-green-400';
    } else if (fromStatus === 'active' || toStatus === 'active') {
      return 'bg-blue-600 dark:bg-blue-400';
    } else {
      return 'bg-gray-300 dark:bg-gray-700';
    }
  };

  if (orientation === 'horizontal') {
    return (
      <div className={`flex items-center ${className}`}>
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            {/* Step */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  flex items-center justify-center
                  w-10 h-10 rounded-full border-2
                  ${getStepColor(step.status)}
                  transition-all duration-200
                `}
              >
                {getStepIcon(step.status)}
              </div>
              <span className="mt-2 text-xs text-gray-600 dark:text-gray-400 text-center max-w-[100px]">
                {step.label}
              </span>
            </div>

            {/* Connector */}
            {index < steps.length - 1 && (
              <div className="flex-1 mx-2">
                <div
                  className={`
                    h-0.5
                    ${getConnectorColor(step.status, steps[index + 1].status)}
                    transition-colors duration-200
                  `}
                />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    );
  }

  // Vertical orientation
  return (
    <div className={`flex flex-col ${className}`}>
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          {/* Step */}
          <div className="flex items-start gap-3">
            <div
              className={`
                flex items-center justify-center
                w-10 h-10 rounded-full border-2 flex-shrink-0
                ${getStepColor(step.status)}
                transition-all duration-200
              `}
            >
              {getStepIcon(step.status)}
            </div>
            <div className="flex-1 pt-2">
              <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                {step.label}
              </span>
            </div>
          </div>

          {/* Connector */}
          {index < steps.length - 1 && (
            <div className="flex justify-start ml-5">
              <div
                className={`
                  w-0.5 h-8
                  ${getConnectorColor(step.status, steps[index + 1].status)}
                  transition-colors duration-200
                `}
              />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

/**
 * Progress card for long-running operations
 */
interface ProgressCardProps {
  title: string;
  progress: number; // 0-100
  description?: string;
  estimatedTimeRemaining?: number; // seconds
  onCancel?: () => void;
  className?: string;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({
  title,
  progress,
  description,
  estimatedTimeRemaining,
  onCancel,
  className = ''
}) => {
  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(0)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${minutes}m ${secs.toFixed(0)}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 ${className}`}>
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h3>
          {description && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {description}
            </p>
          )}
        </div>

        {onCancel && (
          <button
            onClick={onCancel}
            className="text-sm text-red-600 dark:text-red-400 hover:underline"
          >
            Cancel
          </button>
        )}
      </div>

      <ProgressBar value={progress} showPercentage />

      {estimatedTimeRemaining !== undefined && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Estimated time remaining: {formatTime(estimatedTimeRemaining)}
        </div>
      )}
    </div>
  );
};

/**
 * Example usage component
 */
export const ProgressIndicatorExample: React.FC = () => {
  const [progress, setProgress] = React.useState(0);
  const [steps, setSteps] = React.useState<Step[]>([
    { id: '1', label: 'Initialize', status: 'completed' },
    { id: '2', label: 'Process', status: 'active' },
    { id: '3', label: 'Validate', status: 'pending' },
    { id: '4', label: 'Complete', status: 'pending' },
  ]);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + 1;
        if (next >= 100) {
          clearInterval(timer);
          return 100;
        }
        return next;
      });
    }, 100);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="p-8 space-y-8 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Progress Indicator Examples
      </h1>

      {/* Progress Bar */}
      <div>
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
          Progress Bar
        </h2>
        <div className="space-y-4">
          <ProgressBar value={progress} label="Processing files" />
          <ProgressBar value={75} label="Medium size" size="md" color="green" />
          <ProgressBar value={50} label="Large size" size="lg" color="yellow" />
        </div>
      </div>

      {/* Progress Spinner */}
      <div>
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
          Progress Spinner
        </h2>
        <div className="space-y-4">
          <ProgressSpinner label="Loading data..." />
          <ProgressSpinner label="Small spinner" size="sm" />
          <ProgressSpinner label="Large spinner" size="lg" />
        </div>
      </div>

      {/* Progress Ring */}
      <div>
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
          Progress Ring
        </h2>
        <div className="flex gap-8">
          <ProgressRing value={progress} label="Processing" />
          <ProgressRing value={75} color="green" label="Success" size={100} />
          <ProgressRing value={33} color="yellow" label="Warning" size={80} />
        </div>
      </div>

      {/* Step Progress */}
      <div>
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
          Step Progress
        </h2>
        <div className="space-y-8">
          <StepProgress steps={steps} orientation="horizontal" />
          <StepProgress steps={steps} orientation="vertical" />
        </div>
      </div>

      {/* Progress Card */}
      <div>
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
          Progress Card
        </h2>
        <ProgressCard
          title="Training Neural Network"
          progress={progress}
          description="Epoch 45/100"
          estimatedTimeRemaining={125}
          onCancel={() => alert('Cancelled')}
        />
      </div>
    </div>
  );
};
