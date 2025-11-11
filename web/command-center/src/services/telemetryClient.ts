import { telemetryDashboards, type TelemetryDashboard } from '../../analytics';

export interface SurveyResponsePayload {
  surveyId: string;
  ratingAverage?: number;
  notes?: string;
  submittedAt: Date;
}

export interface TelemetryEventPayload {
  metricId: string;
  value: number;
  recordedAt: Date;
}

interface SurveyStats {
  responses: number;
  rollingAverage: number;
}

interface MetricStats {
  samples: number;
  latestValue: number;
}

export class TelemetryClient {
  private surveyStats = new Map<string, SurveyStats>();
  private metricStats = new Map<string, MetricStats>();
  private dashboards: TelemetryDashboard[];

  constructor(dashboards: TelemetryDashboard[] = telemetryDashboards) {
    this.dashboards = dashboards;
  }

  submitSurveyResponse(payload: SurveyResponsePayload): SurveyStats {
    const current = this.surveyStats.get(payload.surveyId) ?? { responses: 0, rollingAverage: 0 };
    const responses = current.responses + 1;
    const rollingAverage = this.computeRollingAverage(current, payload.ratingAverage ?? current.rollingAverage, responses);

    const stats = { responses, rollingAverage };
    this.surveyStats.set(payload.surveyId, stats);
    return stats;
  }

  recordTelemetryEvent(payload: TelemetryEventPayload): MetricStats {
    const current = this.metricStats.get(payload.metricId) ?? { samples: 0, latestValue: payload.value };
    const samples = current.samples + 1;
    const stats = { samples, latestValue: payload.value };
    this.metricStats.set(payload.metricId, stats);
    return stats;
  }

  getSurveyStats(): Map<string, SurveyStats> {
    return new Map(this.surveyStats);
  }

  getMetricStats(): Map<string, MetricStats> {
    return new Map(this.metricStats);
  }

  getDashboards(): TelemetryDashboard[] {
    return this.dashboards;
  }

  private computeRollingAverage(current: SurveyStats, newValue: number, responses: number): number {
    if (responses === 0) {
      return newValue;
    }

    if (current.responses === 0) {
      return newValue;
    }

    const total = current.rollingAverage * current.responses + newValue;
    return total / responses;
  }
}
