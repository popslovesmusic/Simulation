import { useEffect, useRef, useState } from 'react';

type TelemetryPoint = {
  t: number;
  h: number;
};

type StreamMessage = {
  type: 'telemetry' | 'status' | 'error';
  payload: TelemetryPoint | { status: string } | { message: string };
};

export function useWaveformStream(missionId: string | null) {
  const [data, setData] = useState<TelemetryPoint[]>([]);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'streaming' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!missionId) {
      setData([]);
      setStatus('disconnected');
      wsRef.current?.close();
      return;
    }

    const ws = new WebSocket(`${window.location.origin.replace('http', 'ws')}/ws/telemetry?missionId=${missionId}`);
    wsRef.current = ws;
    setStatus('connecting');

    ws.onopen = () => {
      setStatus('streaming');
    };

    ws.onmessage = (event) => {
      try {
        const message: StreamMessage = JSON.parse(event.data);
        if (message.type === 'telemetry' && 't' in message.payload && 'h' in message.payload) {
          setData((prev) => [...prev.slice(-1024), message.payload as TelemetryPoint]);
        }
        if (message.type === 'status' && 'status' in message.payload) {
          setStatus(message.payload.status === 'error' ? 'error' : 'streaming');
        }
        if (message.type === 'error') {
          setStatus('error');
        }
      } catch (err) {
        console.error('Failed to parse telemetry frame', err);
        setStatus('error');
      }
    };

    ws.onerror = () => {
      setStatus('error');
    };

    ws.onclose = () => {
      setStatus('disconnected');
    };

    return () => {
      ws.close();
    };
  }, [missionId]);

  return { data, status };
}
