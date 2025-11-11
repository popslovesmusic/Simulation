import type { SurveyDefinition } from './feedbackConfig';
import type { TelemetryDashboard } from './telemetryDashboards';

export interface FeedbackChannel {
  id: string;
  description: string;
  surveys: SurveyDefinition['id'][];
  telemetryDashboards: TelemetryDashboard['id'][];
  successThresholds: {
    id: string;
    description: string;
    target: number;
  }[];
}

export const feedbackChannels: FeedbackChannel[] = [
  {
    id: 'continuous-wave-loop',
    description: 'Feedback path for mission operators monitoring continuous wave detections.',
    surveys: ['mission-ops-experience'],
    telemetryDashboards: ['continuous-wave-ops'],
    successThresholds: [
      {
        id: 'cw-response-rate',
        description: 'Maintain ≥60% survey response rate among mission operators.',
        target: 0.6
      },
      {
        id: 'cw-latency-target',
        description: 'Keep alert latency p95 under 90 seconds.',
        target: 90
      }
    ]
  },
  {
    id: 'science-alignment-loop',
    description: 'Feedback path uniting science council priorities with research execution.',
    surveys: ['science-roadmap-alignment'],
    telemetryDashboards: ['echo-search-portfolio', 'cmb-imprint-insights'],
    successThresholds: [
      {
        id: 'science-response-rate',
        description: 'Reach ≥50% response rate from science council members.',
        target: 0.5
      },
      {
        id: 'echo-false-positive-cap',
        description: 'Hold false positive rate below 3%.',
        target: 0.03
      },
      {
        id: 'cmb-contamination-cap',
        description: 'Keep B-mode contamination at or below 5%.',
        target: 0.05
      }
    ]
  }
];
