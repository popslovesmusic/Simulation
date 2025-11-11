import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useWaveformStream } from '../hooks/useWaveformStream';

type WaveformPlotProps = {
  missionId: string | null;
};

export function WaveformPlot({ missionId }: WaveformPlotProps) {
  const { t } = useTranslation();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { data, status } = useWaveformStream(missionId);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    const { width, height } = canvas;
    context.clearRect(0, 0, width, height);

    context.strokeStyle = 'rgba(93, 134, 255, 0.9)';
    context.lineWidth = 2;
    context.beginPath();

    if (data.length === 0) {
      context.moveTo(0, height / 2);
      context.lineTo(width, height / 2);
      context.stroke();
      return;
    }

    const maxAmplitude = Math.max(...data.map((d) => Math.abs(d.h))) || 1;
    const horizontalScale = width / Math.max(data.length - 1, 1);

    data.forEach((point, index) => {
      const x = index * horizontalScale;
      const normalized = point.h / maxAmplitude;
      const y = height / 2 - (normalized * height) / 2.2;
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });

    context.stroke();
  }, [data]);

  return (
    <section className="panel" aria-labelledby="waveform-title">
      <header>
        <div className="section-title" id="waveform-title">
          <span aria-hidden="true">📡</span>
          <span>{t('waveform.title')}</span>
        </div>
        <span aria-live="polite">{status}</span>
      </header>
      {!missionId && <p>{t('waveform.empty')}</p>}
      <canvas
        ref={canvasRef}
        width={640}
        height={280}
        aria-label={t('waveform.ariaLabel')}
        role="img"
        className="waveform-canvas"
      />
      <p>{t('waveform.legend')}</p>
    </section>
  );
}
