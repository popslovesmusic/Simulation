import { Suspense, useState } from 'react';
import { MissionSelection } from './components/MissionSelection';
import { RunControlPanel } from './components/RunControlPanel';
import { WaveformPlot } from './components/WaveformPlot';
import { MissionBrief } from './components/MissionBrief';
import { useTranslation } from 'react-i18next';
import { SymbolicsPanel } from './playground/symbolics';
import { TutorialNavigator } from './modules/tutorials/TutorialNavigator';
import { SessionPanel } from './modules/collaboration/SessionPanel';

export default function App() {
  const { t } = useTranslation();
  const [selectedMissionId, setSelectedMissionId] = useState<string | null>(null);
  const [selectedEngine, setSelectedEngine] = useState<string | null>(null);

  return (
    <div className="app-shell" role="application" aria-label={t('app.title')}>
      <header className="app-header" aria-live="polite">
        <h1>{t('app.title')}</h1>
        <p>{t('app.subtitle')}</p>
      </header>
      <main className="app-main">
        <section className="app-column">
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
        </section>
        <section className="app-column">
          <RunControlPanel
            missionId={selectedMissionId}
            engine={selectedEngine}
            onMissionUpdate={setSelectedMissionId}
          />
          <WaveformPlot missionId={selectedMissionId} />
        </section>
        <section className="app-column app-column--playground">
          <SymbolicsPanel />
          <TutorialNavigator />
          <SessionPanel />
        </section>
      </main>
    </div>
  );
}
