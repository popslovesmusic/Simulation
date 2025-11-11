import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import katex from 'katex';

interface MissionBriefProps {
  missionId: string | null;
}

export function MissionBrief({ missionId }: MissionBriefProps) {
  const { t } = useTranslation();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['mission-detail', missionId],
    queryFn: () => (missionId ? apiClient.getMissionDetail(missionId) : Promise.resolve(null)),
    enabled: Boolean(missionId)
  });

  const renderedLatex = useMemo(() => {
    if (!data?.brief_latex) return null;
    try {
      return {
        __html: katex.renderToString(data.brief_latex, {
          throwOnError: false,
          displayMode: true,
          output: 'html'
        })
      };
    } catch (err) {
      console.error('Failed to render LaTeX brief', err);
      return null;
    }
  }, [data?.brief_latex]);

  return (
    <article className="panel" aria-labelledby="mission-brief-title">
      <header>
        <div className="section-title" id="mission-brief-title">
          <span aria-hidden="true">📄</span>
          <span>{t('missionBrief.title')}</span>
        </div>
      </header>
      {!missionId && <p>{t('missionBrief.empty')}</p>}
      {isLoading && <p aria-live="polite">{t('app.loadingBrief')}</p>}
      {isError && <p role="alert">{(error as Error).message}</p>}
      {data && (
        <div>
          {data.brief_markdown && <p>{data.brief_markdown}</p>}
          {renderedLatex && <div className="katex-display" aria-hidden="true" dangerouslySetInnerHTML={renderedLatex} />}
          {data.brief_latex && (
            <p className="sr-only" aria-live="polite">
              {data.brief_latex}
            </p>
          )}
        </div>
      )}
    </article>
  );
}
