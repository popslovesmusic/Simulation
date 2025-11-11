import { useMemo, useState } from 'react';
import {
  surveyDefinitions,
  telemetryDashboards,
  feedbackChannels,
  type SurveyDefinition,
  type TelemetryDashboard,
  type FeedbackChannel
} from '../../analytics';
import { TelemetryClient } from '../services/telemetryClient';

export interface SurveyFormState {
  ratingAverage?: number;
  notes?: string;
}

export interface FeedbackInsights {
  surveyStats: Map<string, { responses: number; rollingAverage: number }>;
  metricStats: Map<string, { samples: number; latestValue: number }>;
  dashboards: TelemetryDashboard[];
  surveys: SurveyDefinition[];
  channels: FeedbackChannel[];
  submitSurvey: (surveyId: string, state: SurveyFormState) => void;
  simulateMetric: (metricId: string, value: number) => void;
}

export function useFeedbackLoop(): FeedbackInsights {
  const telemetryClient = useMemo(() => new TelemetryClient(telemetryDashboards), []);
  const [surveyStats, setSurveyStats] = useState(telemetryClient.getSurveyStats());
  const [metricStats, setMetricStats] = useState(telemetryClient.getMetricStats());

  const submitSurvey = (surveyId: string, state: SurveyFormState) => {
    const response = telemetryClient.submitSurveyResponse({
      surveyId,
      ratingAverage: state.ratingAverage,
      notes: state.notes,
      submittedAt: new Date()
    });
    const nextStats = new Map(surveyStats);
    nextStats.set(surveyId, response);
    setSurveyStats(nextStats);
  };

  const simulateMetric = (metricId: string, value: number) => {
    const response = telemetryClient.recordTelemetryEvent({
      metricId,
      value,
      recordedAt: new Date()
    });
    const nextStats = new Map(metricStats);
    nextStats.set(metricId, response);
    setMetricStats(nextStats);
  };

  return {
    surveyStats,
    metricStats,
    dashboards: telemetryClient.getDashboards(),
    surveys: surveyDefinitions,
    channels: feedbackChannels,
    submitSurvey,
    simulateMetric
  };
}
