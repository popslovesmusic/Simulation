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
