export type SurveyQuestionType = 'rating' | 'likert' | 'multi-select' | 'text';

export interface SurveyQuestion {
  id: string;
  prompt: string;
  type: SurveyQuestionType;
  scale?: number;
  options?: string[];
  successSignal?: string;
}

export interface SurveySuccessMetric {
  targetResponseRate: number;
  satisfactionScoreTarget: number;
  owner: string;
}

export interface SurveyDefinition {
  id: string;
  title: string;
  cadence: 'weekly' | 'biweekly' | 'monthly';
  audience: 'mission-ops' | 'science' | 'platform';
  questions: SurveyQuestion[];
  successMetrics: SurveySuccessMetric;
  backlogLink: string;
}

export const surveyDefinitions: SurveyDefinition[] = [
  {
    id: 'mission-ops-experience',
    title: 'Mission Operations Experience',
    cadence: 'biweekly',
    audience: 'mission-ops',
    questions: [
      {
        id: 'workflow-confidence',
        prompt: 'How confident are you executing mission workflows in the Command Center?',
        type: 'likert',
        scale: 5,
        successSignal: 'Confidence scores ≥4 indicate frictionless workflows.'
      },
      {
        id: 'alert-latency',
        prompt: 'Rate satisfaction with alert latency for continuous wave detections.',
        type: 'rating',
        scale: 5,
        successSignal: 'Track alignment with ≤90 second latency target.'
      },
      {
        id: 'open-feedback',
        prompt: 'What blocked or accelerated your work this sprint?',
        type: 'text'
      }
    ],
    successMetrics: {
      targetResponseRate: 0.6,
      satisfactionScoreTarget: 4.2,
      owner: 'Command Center Product'
    },
    backlogLink: 'analysis/projects/continuous-wave-detection'
  },
  {
    id: 'science-roadmap-alignment',
    title: 'Science Roadmap Alignment',
    cadence: 'monthly',
    audience: 'science',
    questions: [
      {
        id: 'echo-priority',
        prompt: 'Rank the priority of echo search investigations for upcoming sprints.',
        type: 'multi-select',
        options: ['High priority', 'Needs more evidence', 'Defer to next quarter'],
        successSignal: 'Priorities feed echo search review log.'
      },
      {
        id: 'cmb-confidence',
        prompt: 'How confident are you in the current CMB imprint mitigation approach?',
        type: 'likert',
        scale: 5,
        successSignal: 'Confidence <3 triggers security council review.'
      },
      {
        id: 'science-requests',
        prompt: 'List additional analyses or tooling required.',
        type: 'text'
      }
    ],
    successMetrics: {
      targetResponseRate: 0.5,
      satisfactionScoreTarget: 4,
      owner: 'Science Council'
    },
    backlogLink: 'analysis/projects/cmb-imprint-analysis'
  }
];
