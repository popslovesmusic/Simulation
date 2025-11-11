import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  GlossaryEntry,
  TutorialDocument,
  TutorialSummary,
  apiClient,
} from '../../services/apiClient';

const STORAGE_KEY = 'command-center.tutorial-progress';

type ProgressRecord = Record<string, { completed: boolean; lastVisited: string }>;

function loadProgress(): ProgressRecord {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ProgressRecord) : {};
  } catch (error) {
    console.warn('Failed to read tutorial progress', error);
    return {};
  }
}

function persistProgress(progress: ProgressRecord) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch (error) {
    console.warn('Failed to persist tutorial progress', error);
  }
}

export function TutorialNavigator() {
  const [tutorials, setTutorials] = useState<TutorialSummary[]>([]);
  const [glossary, setGlossary] = useState<GlossaryEntry[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [document, setDocument] = useState<TutorialDocument | null>(null);
  const [progress, setProgress] = useState<ProgressRecord>(() => loadProgress());
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .getTutorials()
      .then((data) => {
        setTutorials(data.tutorials);
        setSelectedSlug((previous) => previous ?? data.tutorials[0]?.slug ?? null);
      })
      .catch((err) => setError(err.message));

    apiClient
      .getGlossary()
      .then((data) => setGlossary(data.glossary))
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedSlug) return;
    apiClient
      .getTutorial(selectedSlug)
      .then((doc) => {
        setDocument(doc);
        const stamp = new Date().toISOString();
        setProgress((prev) => {
          const next = {
            ...prev,
            [selectedSlug]: {
              completed: prev[selectedSlug]?.completed ?? false,
              lastVisited: stamp,
            },
          };
          persistProgress(next);
          return next;
        });
      })
      .catch((err) => setError(err.message));
  }, [selectedSlug]);

  const toggleCompleted = useCallback(() => {
    if (!selectedSlug) return;
    setProgress((prev) => {
      const current = prev[selectedSlug] ?? { completed: false, lastVisited: new Date().toISOString() };
      const next = {
        ...prev,
        [selectedSlug]: { ...current, completed: !current.completed, lastVisited: new Date().toISOString() },
      };
      persistProgress(next);
      return next;
    });
  }, [selectedSlug]);

  const glossaryIndex = useMemo(() => glossary.slice(0, 5), [glossary]);

  return (
    <section className="playground-panel" aria-label="Tutorials and glossary">
      <header className="panel-header">
        <h3>Tutorials &amp; Glossary</h3>
        <p>Track Stage 2 learning progress while reviewing key terminology.</p>
      </header>
      <div className="panel-body tutorials-body">
        {error && <p className="tutorial-error">{error}</p>}
        <div className="tutorial-layout">
          <aside className="tutorial-list">
            <h4>Walkthroughs</h4>
            <ul>
              {tutorials.map((tutorial) => {
                const state = progress[tutorial.slug];
                return (
                  <li key={tutorial.slug}>
                    <button
                      type="button"
                      className={tutorial.slug === selectedSlug ? 'active' : ''}
                      onClick={() => setSelectedSlug(tutorial.slug)}
                    >
                      {tutorial.title}
                      {state?.completed && <span className="badge">Done</span>}
                    </button>
                    <p>{tutorial.summary}</p>
                  </li>
                );
              })}
            </ul>
          </aside>
          <article className="tutorial-content">
            {document ? (
              <>
                <header>
                  <h4>{document.title}</h4>
                  <button type="button" onClick={toggleCompleted}>
                    {progress[selectedSlug ?? '']?.completed ? 'Mark as in progress' : 'Mark as complete'}
                  </button>
                </header>
                <pre>{document.content}</pre>
              </>
            ) : (
              <p>Select a tutorial to begin.</p>
            )}
          </article>
        </div>
        <footer className="tutorial-glossary">
          <h4>Glossary Preview</h4>
          <dl>
            {glossaryIndex.map((entry) => (
              <div key={entry.slug}>
                <dt>{entry.title}</dt>
                <dd>{entry.summary}</dd>
              </div>
            ))}
          </dl>
        </footer>
      </div>
    </section>
  );
}
