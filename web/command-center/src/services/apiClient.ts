export type MissionSummary = {
  id: string;
  name: string;
  engine: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'terminated';
  created_at: string;
};

export type MissionDetail = MissionSummary & {
  parameters: Record<string, unknown>;
  brief_markdown?: string;
  brief_latex?: string;
};

export type MissionCommand = 'start' | 'pause' | 'resume' | 'abort';

export type SymbolicContext = {
  functions: string[];
  constants: string[];
  operations: string[];
  examples: string[];
};

export type SymbolicEvaluationRequest = {
  expression: string;
  variables: Record<string, number>;
  operations: string[];
  assumptions?: Record<string, Record<string, boolean>>;
};

export type SymbolicEvaluationResponse = {
  status: 'ok';
  result: {
    repr?: string;
    latex?: string;
    simplified?: { text: string; latex: string };
    numeric?: number | string;
    derivative?: { text: string; latex: string };
    integral?: { text: string; latex: string };
  };
  operations: string[];
  availableOperations: string[];
};

export type TutorialSummary = {
  slug: string;
  title: string;
  summary: string;
};

export type TutorialDocument = {
  title: string;
  content: string;
};

export type GlossaryEntry = {
  slug: string;
  title: string;
  summary: string;
  type?: string;
};

export type SessionNote = {
  id: string;
  author: string;
  content: string;
  created_at: string;
};

export type SessionDocument = {
  id: string;
  name?: string;
  mission_id?: string;
  engine?: string;
  collaborators?: string[];
  payload?: Record<string, unknown>;
  notes?: SessionNote[];
  created_at?: string;
  updated_at?: string;
};

export type SessionPayload = {
  name?: string;
  mission_id?: string;
  engine?: string;
  collaborators?: string[];
  payload?: Record<string, unknown>;
};

const authToken = () => localStorage.getItem('command-center-token') ?? '';

async function request<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authToken()}`,
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API ${response.status}: ${errorText}`);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  async getMissions(): Promise<MissionSummary[]> {
    const data = await request<{ missions: MissionSummary[] }>('/api/missions');
    return data.missions;
  },
  async getMissionDetail(id: string): Promise<MissionDetail> {
    return request<MissionDetail>(`/api/missions/${id}`);
  },
  async sendMissionCommand(id: string, command: MissionCommand): Promise<MissionDetail> {
    return request<MissionDetail>(`/api/missions/${id}/commands`, {
      method: 'POST',
      body: JSON.stringify({ command })
    });
  },
  async createMission(payload: Partial<MissionDetail>): Promise<MissionDetail> {
    return request<MissionDetail>('/api/missions', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  async getSymbolicContext(): Promise<SymbolicContext> {
    return request<SymbolicContext>('/api/playground/symbolics/context');
  },
  async evaluateSymbolicExpression(payload: SymbolicEvaluationRequest): Promise<SymbolicEvaluationResponse> {
    return request<SymbolicEvaluationResponse>('/api/playground/symbolics/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  async getTutorials(): Promise<{ tutorials: TutorialSummary[] }> {
    return request<{ tutorials: TutorialSummary[] }>('/api/playground/tutorials');
  },
  async getTutorial(slug: string): Promise<TutorialDocument> {
    return request<TutorialDocument>(`/api/playground/tutorials/${slug}`);
  },
  async getGlossary(): Promise<{ glossary: GlossaryEntry[] }> {
    return request<{ glossary: GlossaryEntry[] }>('/api/playground/glossary');
  },
  async listSessions(): Promise<{ sessions: SessionDocument[] }> {
    return request<{ sessions: SessionDocument[] }>('/api/playground/sessions');
  },
  async getSession(id: string): Promise<SessionDocument> {
    return request<SessionDocument>(`/api/playground/sessions/${id}`);
  },
  async saveSession(id: string, payload: SessionPayload): Promise<SessionDocument> {
    return request<SessionDocument>(`/api/playground/sessions/${id}`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  async addSessionNote(id: string, payload: { author?: string; content: string }): Promise<SessionNote> {
    return request<SessionNote>(`/api/playground/sessions/${id}/notes`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
};
