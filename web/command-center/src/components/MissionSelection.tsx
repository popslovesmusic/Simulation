import { useQuery } from '@tanstack/react-query';
import { apiClient, MissionSummary } from '../services/apiClient';
import { useTranslation } from 'react-i18next';

type MissionSelectionProps = {
  selectedMissionId: string | null;
  onMissionSelected: (mission: MissionSummary) => void;
};

export function MissionSelection({ selectedMissionId, onMissionSelected }: MissionSelectionProps) {
  const { t } = useTranslation();
  const { data, isLoading, refetch, isError, error } = useQuery({
    queryKey: ['missions'],
    queryFn: () => apiClient.getMissions(),
    staleTime: 30_000
  });

  return (
    <section className="panel" aria-labelledby="mission-selection-title">
      <header>
        <div className="section-title" id="mission-selection-title">
          <span aria-hidden="true">🛰️</span>
          <span>{t('missionSelection.title')}</span>
        </div>
        <button className="secondary" type="button" onClick={() => refetch()}>
          {t('missionSelection.refresh')}
        </button>
      </header>
      {isLoading && <p aria-live="polite">{t('app.loadingBrief')}</p>}
      {isError && <p role="alert">{(error as Error).message}</p>}
      {!isLoading && !isError && (!data || data.length === 0) && <p>{t('missionSelection.empty')}</p>}
      <ul role="listbox" aria-label={t('missionSelection.ariaLabel')} className="list">
        {data?.map((mission) => (
          <li
            key={mission.id}
            role="option"
            aria-selected={mission.id === selectedMissionId}
            className="list-item"
            tabIndex={0}
            onClick={() => onMissionSelected(mission)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onMissionSelected(mission);
              }
            }}
          >
            <strong>{mission.name}</strong>
            <span>{mission.engine}</span>
            <span>{new Date(mission.created_at).toLocaleString()}</span>
            <span className="sr-only">{t('missionSelection.select', { name: mission.name })}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
