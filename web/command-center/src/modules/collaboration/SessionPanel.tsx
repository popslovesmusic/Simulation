import { FormEvent, useEffect, useState } from 'react';
import {
  SessionDocument,
  SessionNote,
  SessionPayload,
  apiClient,
} from '../../services/apiClient';

const EMPTY_SESSION: SessionPayload = {
  name: '',
  mission_id: '',
  engine: '',
  collaborators: [],
  payload: {},
};

export function SessionPanel() {
  const [sessions, setSessions] = useState<SessionDocument[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [draft, setDraft] = useState<SessionPayload>(EMPTY_SESSION);
  const [notes, setNotes] = useState<SessionNote[]>([]);
  const [noteContent, setNoteContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiClient
      .listSessions()
      .then((data) => setSessions(data.sessions))
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    apiClient
      .getSession(selectedId)
      .then((session) => {
        setDraft({
          name: session.name ?? '',
          mission_id: session.mission_id ?? '',
          engine: session.engine ?? '',
          collaborators: session.collaborators ?? [],
          payload: session.payload ?? {},
        });
        setNotes(session.notes ?? []);
      })
      .catch((err) => setError(err.message));
  }, [selectedId]);

  const refreshSessions = () => {
    apiClient
      .listSessions()
      .then((data) => setSessions(data.sessions))
      .catch((err) => setError(err.message));
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!selectedId) {
      setError('Provide a session identifier to save your workspace.');
      return;
    }
    setSaving(true);
    apiClient
      .saveSession(selectedId, draft)
      .then((session) => {
        setNotes(session.notes ?? []);
        refreshSessions();
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setSaving(false));
  };

  const handleAddNote = (event: FormEvent) => {
    event.preventDefault();
    if (!selectedId || !noteContent.trim()) return;
    apiClient
      .addSessionNote(selectedId, { author: draft.collaborators?.[0] ?? 'reviewer', content: noteContent })
      .then((note) => {
        setNotes((prev) => [...prev, note]);
        setNoteContent('');
        refreshSessions();
      })
      .catch((err) => setError(err.message));
  };

  return (
    <section className="playground-panel" aria-label="Sessions & collaboration">
      <header className="panel-header">
        <h3>Sessions &amp; Collaboration</h3>
        <p>Persist mission sandboxes and coordinate review notes.</p>
      </header>
      <div className="panel-body collaboration-body">
        {error && <p className="collaboration-error">{error}</p>}
        <div className="collaboration-layout">
          <aside>
            <h4>Saved sessions</h4>
            <ul>
              {sessions.map((session) => (
                <li key={session.id}>
                  <button
                    type="button"
                    className={session.id === selectedId ? 'active' : ''}
                    onClick={() => setSelectedId(session.id)}
                  >
                    <strong>{session.name || session.id}</strong>
                    <span>{new Date(session.updated_at ?? session.created_at ?? '').toLocaleString()}</span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>
          <div className="collaboration-editor">
            <form onSubmit={handleSubmit}>
              <label>
                <span>Session ID</span>
                <input
                  type="text"
                  value={selectedId}
                  onChange={(event) => setSelectedId(event.target.value)}
                  placeholder="stage2-review"
                />
              </label>
              <label>
                <span>Display name</span>
                <input
                  type="text"
                  value={draft.name}
                  onChange={(event) => setDraft({ ...draft, name: event.target.value })}
                />
              </label>
              <label>
                <span>Mission ID</span>
                <input
                  type="text"
                  value={draft.mission_id}
                  onChange={(event) => setDraft({ ...draft, mission_id: event.target.value })}
                />
              </label>
              <label>
                <span>Engine</span>
                <input
                  type="text"
                  value={draft.engine}
                  onChange={(event) => setDraft({ ...draft, engine: event.target.value })}
                />
              </label>
              <label>
                <span>Collaborators (comma separated)</span>
                <input
                  type="text"
                  value={draft.collaborators?.join(', ') ?? ''}
                  onChange={(event) =>
                    setDraft({ ...draft, collaborators: event.target.value.split(',').map((item) => item.trim()).filter(Boolean) })
                  }
                />
              </label>
              <label>
                <span>Payload (JSON)</span>
                <textarea
                  rows={4}
                  value={JSON.stringify(draft.payload ?? {}, null, 2)}
                  onChange={(event) => {
                    try {
                      const parsed = JSON.parse(event.target.value || '{}');
                      setDraft({ ...draft, payload: parsed });
                      setError(null);
                    } catch (parseError) {
                      setError('Payload must be valid JSON.');
                    }
                  }}
                />
              </label>
              <button type="submit" disabled={saving}>
                {saving ? 'Saving…' : 'Save session'}
              </button>
            </form>
            <section className="collaboration-notes" aria-label="Session notes">
              <h4>Shared notes</h4>
              <ul>
                {notes.map((note) => (
                  <li key={note.id}>
                    <strong>{note.author}</strong>
                    <time>{new Date(note.created_at).toLocaleString()}</time>
                    <p>{note.content}</p>
                  </li>
                ))}
              </ul>
              <form onSubmit={handleAddNote} className="note-form">
                <textarea
                  rows={3}
                  placeholder="Record review findings"
                  value={noteContent}
                  onChange={(event) => setNoteContent(event.target.value)}
                />
                <button type="submit">Add note</button>
              </form>
            </section>
          </div>
        </div>
      </div>
    </section>
  );
}
