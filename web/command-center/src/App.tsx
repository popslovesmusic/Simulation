import { Suspense, useState, useEffect, useCallback } from 'react';
import { MissionSelection } from './components/MissionSelection';
import { RunControlPanel } from './components/RunControlPanel';
import { WaveformPlot } from './components/WaveformPlot';
import { MissionBrief } from './components/MissionBrief';
import { useTranslation } from 'react-i18next';
import { SymbolicsPanel } from './playground/symbolics';
import { TutorialNavigator } from './modules/tutorials/TutorialNavigator';
import { SessionPanel } from './modules/collaboration/SessionPanel';
import { FeedbackDashboard } from './components/FeedbackDashboard';
import { Grid } from './components/Grid';
import { ModelPanel } from './components/ModelPanel';
import { apiClient } from './services/apiClient';

export default function App() {
  const { t } = useTranslation();
  const [selectedMissionId, setSelectedMissionId] = useState<string | null>(null);
  const [selectedEngine, setSelectedEngine] = useState<string | null>(null);
  const [availableEngines, setAvailableEngines] = useState<string[]>([]);
  const [modelParameters, setModelParameters] = useState<Record<string, unknown>>({});
  const [creatingMission, setCreatingMission] = useState(false);

  // Load available engines on mount
  useEffect(() => {
    fetch('/api/engines', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('command-center-token') ?? ''}`,
      },
    })
      .then((res) => res.json())
      .then((data) => setAvailableEngines(data.engines || []))
      .catch((err) => console.error('Failed to load engines:', err));
  }, []);

  // Handle mission creation from ModelPanel
  const handleCreateMission = useCallback(async () => {
    if (!selectedEngine) {
      alert('Please select an engine first');
      return;
    }

    setCreatingMission(true);
    try {
      const mission = await apiClient.createMission({
        name: `${selectedEngine} Mission ${new Date().toLocaleTimeString()}`,
        engine: selectedEngine,
        parameters: modelParameters,
        brief_markdown: `Auto-generated mission for ${selectedEngine}`,
      });

      setSelectedMissionId(mission.id);
      setSelectedEngine(mission.engine);
      console.log('Mission created:', mission);
    } catch (error) {
      console.error('Failed to create mission:', error);
      alert(`Failed to create mission: ${(error as Error).message}`);
    } finally {
      setCreatingMission(false);
    }
  }, [selectedEngine, modelParameters]);

  return (
    <div className="app-shell" role="application" aria-label={t('app.title')}>
      <header className="app-header" aria-live="polite">
        <div className="header-content">
          <div className="header-text">
            <h1>{t('app.title')}</h1>
            <p>{t('app.subtitle')}</p>
          </div>
          <div className="engine-selector">
            <label htmlFor="engine-select">
              <span>Engine:</span>
              <select
                id="engine-select"
                value={selectedEngine ?? ''}
                onChange={(e) => setSelectedEngine(e.target.value || null)}
                aria-label="Select simulation engine"
              >
                <option value="">Select engine...</option>
                {availableEngines.map((engine) => (
                  <option key={engine} value={engine}>
                    {engine}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </header>
      <main className="app-main">
        {/* Left Column: Mission selection, brief, and model configuration */}
        <section className="app-column app-column--left">
          <MissionSelection
            onMissionSelected={(mission) => {
              setSelectedMissionId(mission.id);
              setSelectedEngine(mission.engine);
            }}
            selectedMissionId={selectedMissionId}
          />
          <Suspense fallback={<div>{t('app.loadingBrief')}</div>}>
            <MissionBrief missionId={selectedMissionId} />
          </Suspense>
          <ModelPanel
            engineName={selectedEngine}
            onParameterChange={setModelParameters}
            onCreateMission={handleCreateMission}
            isCreating={creatingMission}
          />
        </section>

        {/* Center Column: Grid and run controls */}
        <section className="app-column app-column--center">
          <Grid rows={100} cols={26} />
          <RunControlPanel
            missionId={selectedMissionId}
            engine={selectedEngine}
            onMissionUpdate={setSelectedMissionId}
          />
        </section>

        {/* Right Column: Waveform and symbolics */}
        <section className="app-column app-column--right">
          <WaveformPlot missionId={selectedMissionId} />
          <SymbolicsPanel />
        </section>

        {/* Playground Column: Tutorials, sessions, feedback */}
        <section className="app-column app-column--playground">
          <TutorialNavigator />
          <SessionPanel />
          <FeedbackDashboard />
        </section>
      </main>
    </div>
  );
}
