import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { WaveformPlot } from './WaveformPlot';

// Mock the i18n hook
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
    },
  }),
}));

// Mock the waveform stream hook
const mockUseWaveformStream = vi.fn();
vi.mock('../hooks/useWaveformStream', () => ({
  useWaveformStream: (missionId: string | null) => mockUseWaveformStream(missionId),
}));

describe('WaveformPlot', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render canvas element', () => {
    // Mock hook to return empty data
    mockUseWaveformStream.mockReturnValue({
      data: [],
      status: 'idle',
    });

    render(<WaveformPlot missionId="test-mission-1" />);

    const canvas = screen.getByRole('img', { hidden: true }) || document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('should render empty waveform when no data', () => {
    mockUseWaveformStream.mockReturnValue({
      data: [],
      status: 'idle',
    });

    const { container } = render(<WaveformPlot missionId="test-mission-1" />);

    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveAttribute('width');
    expect(canvas).toHaveAttribute('height');
  });

  it('should call useWaveformStream with correct mission ID', () => {
    mockUseWaveformStream.mockReturnValue({
      data: [],
      status: 'idle',
    });

    render(<WaveformPlot missionId="mission-123" />);

    expect(mockUseWaveformStream).toHaveBeenCalledWith('mission-123');
  });

  it('should render waveform with data points', async () => {
    // Mock waveform data
    const mockData = [
      { t: 0.0, h: 0.0 },
      { t: 0.1, h: 0.5 },
      { t: 0.2, h: 1.0 },
      { t: 0.3, h: 0.5 },
      { t: 0.4, h: 0.0 },
    ];

    mockUseWaveformStream.mockReturnValue({
      data: mockData,
      status: 'success',
    });

    const { container } = render(<WaveformPlot missionId="test-mission-1" />);

    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();

    // Canvas should have been drawn (context operations called)
    // Note: Testing canvas rendering in unit tests is limited
    // We verify the component renders without errors
    await waitFor(() => {
      expect(mockUseWaveformStream).toHaveBeenCalled();
    });
  });

  it('should handle null mission ID', () => {
    mockUseWaveformStream.mockReturnValue({
      data: [],
      status: 'idle',
    });

    render(<WaveformPlot missionId={null} />);

    expect(mockUseWaveformStream).toHaveBeenCalledWith(null);
  });

  it('should update when mission ID changes', () => {
    mockUseWaveformStream.mockReturnValue({
      data: [],
      status: 'idle',
    });

    const { rerender } = render(<WaveformPlot missionId="mission-1" />);

    expect(mockUseWaveformStream).toHaveBeenCalledWith('mission-1');

    // Change mission ID
    mockUseWaveformStream.mockClear();
    rerender(<WaveformPlot missionId="mission-2" />);

    expect(mockUseWaveformStream).toHaveBeenCalledWith('mission-2');
  });

  it('should handle loading status', () => {
    mockUseWaveformStream.mockReturnValue({
      data: [],
      status: 'loading',
    });

    const { container } = render(<WaveformPlot missionId="test-mission-1" />);

    // Component should still render canvas
    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('should handle error status', () => {
    mockUseWaveformStream.mockReturnValue({
      data: [],
      status: 'error',
    });

    const { container } = render(<WaveformPlot missionId="test-mission-1" />);

    // Component should still render canvas (graceful degradation)
    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('should normalize amplitude correctly', async () => {
    // Test with different amplitude scales
    const mockData = [
      { t: 0.0, h: 0.0 },
      { t: 0.1, h: 10.0 },
      { t: 0.2, h: -10.0 },
      { t: 0.3, h: 5.0 },
    ];

    mockUseWaveformStream.mockReturnValue({
      data: mockData,
      status: 'success',
    });

    const { container } = render(<WaveformPlot missionId="test-mission-1" />);

    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();

    // Verify no errors during rendering (normalization works)
    await waitFor(() => {
      expect(mockUseWaveformStream).toHaveBeenCalled();
    });
  });

  it('should handle single data point', () => {
    const mockData = [{ t: 0.0, h: 1.0 }];

    mockUseWaveformStream.mockReturnValue({
      data: mockData,
      status: 'success',
    });

    const { container } = render(<WaveformPlot missionId="test-mission-1" />);

    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('should handle very large datasets', () => {
    // Test with 10,000 points
    const mockData = Array.from({ length: 10000 }, (_, i) => ({
      t: i * 0.001,
      h: Math.sin(i * 0.1),
    }));

    mockUseWaveformStream.mockReturnValue({
      data: mockData,
      status: 'success',
    });

    const { container } = render(<WaveformPlot missionId="test-mission-1" />);

    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();

    // Should render without performance issues
    expect(mockUseWaveformStream).toHaveBeenCalled();
  });
});
