import { FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useFeedbackLoop, type SurveyFormState } from '../hooks/useFeedbackLoop';

interface SurveyFormStateMap {
  [surveyId: string]: SurveyFormState;
}

interface MetricFormStateMap {
  [metricId: string]: number | undefined;
}

export function FeedbackDashboard() {
  const { t } = useTranslation();
  const { surveys, surveyStats, metricStats, dashboards, channels, submitSurvey, simulateMetric } = useFeedbackLoop();
  const [surveyForms, setSurveyForms] = useState<SurveyFormStateMap>({});
  const [metricForms, setMetricForms] = useState<MetricFormStateMap>({});

  const handleSurveySubmit = (surveyId: string) => (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitSurvey(surveyId, surveyForms[surveyId] ?? {});
  };

  const updateSurveyForm = (surveyId: string, field: keyof SurveyFormState, value: number | string | undefined) => {
    setSurveyForms((previous) => ({
      ...previous,
      [surveyId]: {
        ...previous[surveyId],
        [field]: typeof value === 'number' ? value : value ?? undefined
      }
    }));
  };

  const updateMetricForm = (metricId: string, value: number | undefined) => {
    setMetricForms((previous) => ({
      ...previous,
      [metricId]: value
    }));
  };

  const handleMetricSubmit = (metricId: string) => (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = metricForms[metricId];
    if (value !== undefined) {
      simulateMetric(metricId, value);
    }
  };

  return (
    <section className="playground-panel feedback-dashboard" aria-labelledby="feedback-dashboard-title">
      <div className="panel-header">
        <h3 id="feedback-dashboard-title">{t('feedback.title')}</h3>
        <p>{t('feedback.description')}</p>
      </div>

      <div className="panel-body feedback-body">
        <div className="feedback-surveys">
          <h4>{t('feedback.surveys.title')}</h4>
          {surveys.map((survey) => {
            const stats = surveyStats.get(survey.id);
            const cadenceLabel = t(`feedback.surveys.cadence.${survey.cadence}`);
            const audienceLabel = t(`feedback.surveys.audience.${survey.audience}`);
            return (
              <form key={survey.id} className="feedback-card" onSubmit={handleSurveySubmit(survey.id)}>
                <header>
                  <h5>{survey.title}</h5>
                  <p>
                    {t('feedback.surveys.meta', {
                      cadence: cadenceLabel,
                      audience: audienceLabel
                    })}
                  </p>
                </header>
                <dl>
                  <div>
                    <dt>{t('feedback.surveys.targetResponse')}</dt>
                    <dd>{Math.round(survey.successMetrics.targetResponseRate * 100)}%</dd>
                  </div>
                  <div>
                    <dt>{t('feedback.surveys.targetSatisfaction')}</dt>
                    <dd>{survey.successMetrics.satisfactionScoreTarget.toFixed(1)}</dd>
                  </div>
                  <div>
                    <dt>{t('feedback.surveys.responses')}</dt>
                    <dd>{stats?.responses ?? 0}</dd>
                  </div>
                  <div>
                    <dt>{t('feedback.surveys.averageScore')}</dt>
                    <dd>{stats?.rollingAverage ? stats.rollingAverage.toFixed(2) : '—'}</dd>
                  </div>
                </dl>
                <label className="feedback-label">
                  {t('feedback.surveys.ratingPrompt')}
                  <input
                    type="number"
                    min={1}
                    max={5}
                    step={0.5}
                    value={surveyForms[survey.id]?.ratingAverage ?? ''}
                    onChange={(event) => {
                      const raw = event.target.value;
                      updateSurveyForm(
                        survey.id,
                        'ratingAverage',
                        raw === '' ? undefined : Number(raw)
                      );
                    }}
                    aria-label={t('feedback.surveys.ratingAria')}
                  />
                </label>
                <label className="feedback-label">
                  {t('feedback.surveys.notesPrompt')}
                  <textarea
                    value={surveyForms[survey.id]?.notes ?? ''}
                    onChange={(event) => updateSurveyForm(survey.id, 'notes', event.target.value)}
                    rows={3}
                  />
                </label>
                <button type="submit">{t('feedback.surveys.submit')}</button>
              </form>
            );
          })}
        </div>

        <div className="feedback-metrics">
          <h4>{t('feedback.telemetry.title')}</h4>
          {dashboards.map((dashboard) => (
            <section key={dashboard.id} className="feedback-card">
              <header>
                <h5>{dashboard.title}</h5>
                <p>
                  {t('feedback.telemetry.meta', {
                    cadence: dashboard.reviewCadence,
                    owner: dashboard.owner
                  })}
                </p>
              </header>
              <ul>
                {dashboard.metrics.map((metric) => {
                  const metricStat = metricStats.get(metric.id);
                  return (
                    <li key={metric.id}>
                      <div className="feedback-metric">
                        <div>
                          <strong>{metric.label}</strong>
                          <p>{metric.description}</p>
                        </div>
                        <div className="feedback-metric-stats">
                          <span>
                            {t('feedback.telemetry.target', {
                              value: metric.target,
                              unit: metric.unit,
                              direction: metric.direction === 'below' ? t('feedback.telemetry.directionBelow') : t('feedback.telemetry.directionAbove')
                            })}
                          </span>
                          <span>{metricStat ? metricStat.latestValue : t('feedback.telemetry.noData')}</span>
                        </div>
                        <form className="feedback-metric-form" onSubmit={handleMetricSubmit(metric.id)}>
                          <label>
                            {t('feedback.telemetry.recordLabel')}
                            <input
                              type="number"
                              step="any"
                              value={metricForms[metric.id] ?? ''}
                              onChange={(event) => {
                                const raw = event.target.value;
                                updateMetricForm(metric.id, raw === '' ? undefined : Number(raw));
                              }}
                            />
                          </label>
                          <button type="submit">{t('feedback.telemetry.record')}</button>
                        </form>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>

        <div className="feedback-channels">
          <h4>{t('feedback.channels.title')}</h4>
          <ul>
            {channels.map((channel) => (
              <li key={channel.id}>
                <article className="feedback-card">
                  <header>
                    <h5>{channel.id}</h5>
                    <p>{channel.description}</p>
                  </header>
                  <h6>{t('feedback.channels.surveys')}</h6>
                  <p>{channel.surveys.join(', ')}</p>
                  <h6>{t('feedback.channels.telemetry')}</h6>
                  <p>{channel.telemetryDashboards.join(', ')}</p>
                  <h6>{t('feedback.channels.thresholds')}</h6>
                  <ul>
                    {channel.successThresholds.map((threshold) => (
                      <li key={threshold.id}>
                        <strong>{threshold.description}</strong>: {threshold.target}
                      </li>
                    ))}
                  </ul>
                </article>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
