import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      app: {
        title: 'IGSOA Mission Command Center',
        subtitle: 'Stage 1 operations console for mission orchestration',
        loadingBrief: 'Loading mission brief…'
      },
      missionSelection: {
        title: 'Mission Selection',
        ariaLabel: 'Available missions',
        empty: 'No missions available. Configure a mission to begin.',
        refresh: 'Refresh missions',
        select: 'Select mission {{name}}'
      },
      missionBrief: {
        title: 'Mission Brief',
        empty: 'Select a mission to view its scientific brief.'
      },
      runControl: {
        title: 'Run Control',
        statusLabel: 'Mission status',
        start: 'Start mission',
        resume: 'Resume mission',
        pause: 'Pause mission',
        stop: 'Abort mission',
        noMission: 'Choose a mission to manage lifecycle controls.',
        running: 'Mission is running',
        idle: 'Mission is idle',
        pending: 'Mission is pending start'
      },
      waveform: {
        title: 'Waveform Telemetry',
        empty: 'Telemetry stream not available until a mission is running.',
        ariaLabel: 'Waveform visualization canvas',
        legend: 'Strain amplitude'
      },
      feedback: {
        title: 'User Feedback & Telemetry',
        description: 'Collect surveys and operational metrics to steer the research roadmap.',
        surveys: {
          title: 'Surveys',
          meta: 'Cadence: {{cadence}}, Audience: {{audience}}',
          targetResponse: 'Target response rate',
          targetSatisfaction: 'Target satisfaction score',
          responses: 'Responses submitted',
          averageScore: 'Rolling average score',
          ratingPrompt: 'Average score (1-5)',
          ratingAria: 'Average satisfaction score',
          notesPrompt: 'Supporting notes',
          submit: 'Record response',
          cadence: {
            weekly: 'Weekly',
            biweekly: 'Bi-weekly',
            monthly: 'Monthly'
          },
          audience: {
            'mission-ops': 'Mission operations',
            science: 'Science council',
            platform: 'Platform engineering'
          }
        },
        telemetry: {
          title: 'Telemetry Dashboards',
          meta: 'Review cadence: {{cadence}}, Owner: {{owner}}',
          target: '{{direction}} {{value}} {{unit}}',
          directionBelow: '≤',
          directionAbove: '≥',
          recordLabel: 'Latest sample',
          record: 'Log metric',
          noData: 'No samples yet'
        },
        channels: {
          title: 'Feedback Channels',
          surveys: 'Surveys',
          telemetry: 'Telemetry dashboards',
          thresholds: 'Success thresholds'
        }
      }
    }
  }
};

const detectionOrder = ['querystring', 'navigator'];

if (!i18n.isInitialized) {
  i18n
    .use(initReactI18next)
    .init({
      resources,
      lng: 'en',
      fallbackLng: 'en',
      defaultNS: 'translation',
      detection: { order: detectionOrder },
      interpolation: { escapeValue: false }
    })
    .catch((error) => {
      console.error('Failed to initialize i18n', error);
    });
}

export default i18n;
