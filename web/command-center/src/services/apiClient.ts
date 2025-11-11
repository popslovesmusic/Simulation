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
  }
};
