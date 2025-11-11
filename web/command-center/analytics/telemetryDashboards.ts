export interface TelemetryMetric {
  id: string;
  label: string;
  description: string;
  target: number;
  unit: string;
  direction: 'above' | 'below';
}

export interface TelemetryDashboard {
  id: string;
  title: string;
  metrics: TelemetryMetric[];
  reviewCadence: 'weekly' | 'biweekly' | 'monthly';
  owner: string;
}

export const telemetryDashboards: TelemetryDashboard[] = [
  {
    id: 'continuous-wave-ops',
    title: 'Continuous Wave Detection Health',
    reviewCadence: 'weekly',
    owner: 'Waveform Systems Guild',
    metrics: [
      {
        id: 'cw-latency-p95',
        label: 'Alert Latency (p95)',
        description: 'Time between strain capture and mission alert broadcast.',
        target: 90,
        unit: 'seconds',
        direction: 'below'
      },
      {
        id: 'cw-detection-efficiency',
        label: 'Detection Efficiency @ 1e-25',
        description: 'Recovered continuous wave injections divided by total injections.',
        target: 0.92,
        unit: 'ratio',
        direction: 'above'
      }
    ]
  },
  {
    id: 'echo-search-portfolio',
    title: 'Echo Search Portfolio',
    reviewCadence: 'biweekly',
    owner: 'Research Operations',
    metrics: [
      {
        id: 'echo-false-positive',
        label: 'False Positive Rate',
        description: 'Portion of reviewed echo candidates rejected as glitches.',
        target: 0.03,
        unit: 'ratio',
        direction: 'below'
      },
      {
        id: 'echo-compute-hours',
        label: 'Compute Hours Used',
        description: 'Total GPU/CPU hours consumed during inference runs.',
        target: 320,
        unit: 'hours',
        direction: 'below'
      }
    ]
  },
  {
    id: 'cmb-imprint-insights',
    title: 'CMB Imprint Insights',
    reviewCadence: 'monthly',
    owner: 'Science Council',
    metrics: [
      {
        id: 'cmb-r-tensor-accuracy',
        label: 'Tensor-to-Scalar Accuracy',
        description: 'Absolute difference between estimated and simulated r values.',
        target: 0.002,
        unit: 'Δr',
        direction: 'below'
      },
      {
        id: 'cmb-bmode-contamination',
        label: 'B-mode Contamination',
        description: 'Fraction of detected signal attributed to dust/systematics.',
        target: 0.05,
        unit: 'ratio',
        direction: 'below'
      }
    ]
  }
];
