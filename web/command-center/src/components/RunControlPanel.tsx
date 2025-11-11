import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';

type RunControlPanelProps = {
  missionId: string | null;
  engine: string | null;
  onMissionUpdate: (missionId: string | null) => void;
};

export function RunControlPanel({ missionId, engine, onMissionUpdate }: RunControlPanelProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: ['mission-detail', missionId],
    queryFn: () => (missionId ? apiClient.getMissionDetail(missionId) : Promise.resolve(null)),
    enabled: Boolean(missionId)
  });

  const mutation = useMutation({
    mutationFn: ({ command }: { command: 'start' | 'pause' | 'resume' | 'abort' }) => {
      if (!missionId) throw new Error('Mission required for command');
      return apiClient.sendMissionCommand(missionId, command);
    },
    onSuccess: (updatedMission) => {
      queryClient.setQueryData(['mission-detail', missionId], updatedMission);
      queryClient.invalidateQueries({ queryKey: ['missions'] });
      if (updatedMission.status === 'terminated') {
        onMissionUpdate(null);
      }
    }
  });

  const statusLabel = useMemo(() => {
    if (!data) return null;
    switch (data.status) {
      case 'running':
        return t('runControl.running');
      case 'pending':
        return t('runControl.pending');
      default:
        return t('runControl.idle');
    }
  }, [data, t]);

  const disabled = !missionId || mutation.isPending;

  return (
    <section className="panel" aria-labelledby="run-control-title">
      <header>
        <div className="section-title" id="run-control-title">
          <span aria-hidden="true">🎛️</span>
          <span>{t('runControl.title')}</span>
        </div>
      </header>
      {!missionId && <p>{t('runControl.noMission')}</p>}
      {missionId && (
        <div>
          <p>
            <strong>{t('runControl.statusLabel')}:</strong> {statusLabel}
          </p>
          <p>
            <strong>Engine:</strong> {engine}
          </p>
          <div role="group" aria-label="Mission lifecycle controls" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              className="primary"
              type="button"
              disabled={disabled || data?.status === 'running'}
              onClick={() => mutation.mutate({ command: 'start' })}
            >
              {t('runControl.start')}
            </button>
            <button
              className="secondary"
              type="button"
              disabled={disabled || data?.status !== 'running'}
              onClick={() => mutation.mutate({ command: 'pause' })}
            >
              {t('runControl.pause')}
            </button>
            <button
              className="secondary"
              type="button"
              disabled={disabled || data?.status !== 'paused'}
              onClick={() => mutation.mutate({ command: 'resume' })}
            >
              {t('runControl.resume')}
            </button>
            <button
              className="secondary"
              type="button"
              disabled={disabled}
              onClick={() => mutation.mutate({ command: 'abort' })}
            >
              {t('runControl.stop')}
            </button>
          </div>
          {mutation.isError && <p role="alert">{(mutation.error as Error).message}</p>}
        </div>
      )}
    </section>
  );
}
