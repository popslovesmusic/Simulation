import { useCallback, useRef, useState, useEffect } from 'react';
import { useGridEngine } from './useGridEngine';
import './Grid.css';

interface GridProps {
  rows?: number;
  cols?: number;
  className?: string;
}

const COLUMN_WIDTH = 100;
const ROW_HEIGHT = 28;
const HEADER_HEIGHT = 32;

function getColumnLabel(index: number): string {
  let label = '';
  let n = index;
  while (n >= 0) {
    label = String.fromCharCode(65 + (n % 26)) + label;
    n = Math.floor(n / 26) - 1;
  }
  return label;
}

function getCellId(row: number, col: number): string {
  return `${getColumnLabel(col)}${row + 1}`;
}

export function Grid({ rows = 100, cols = 26, className = '' }: GridProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>(null);
  const [editingCell, setEditingCell] = useState<{ row: number; col: number } | null>(null);
  const [editValue, setEditValue] = useState('');
  const [scrollOffset, setScrollOffset] = useState({ x: 0, y: 0 });

  const {
    cells,
    getCellValue,
    getCellFormula,
    setCellFormula,
    evaluateCell,
    subscribeLiveMetric,
    unsubscribeLiveMetric,
  } = useGridEngine(rows, cols);

  const handleCellClick = useCallback((row: number, col: number) => {
    setSelectedCell({ row, col });
    setEditingCell(null);
  }, []);

  const handleCellDoubleClick = useCallback(
    (row: number, col: number) => {
      setEditingCell({ row, col });
      const cellId = getCellId(row, col);
      const formula = getCellFormula(cellId);
      setEditValue(formula || '');
    },
    [getCellFormula]
  );

  const handleEditKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter' && editingCell) {
        const cellId = getCellId(editingCell.row, editingCell.col);
        setCellFormula(cellId, editValue);
        setEditingCell(null);
        setEditValue('');
      } else if (event.key === 'Escape') {
        setEditingCell(null);
        setEditValue('');
      }
    },
    [editingCell, editValue, setCellFormula]
  );

  const handleCanvasClick = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement>) => {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;

      const x = event.clientX - rect.left + scrollOffset.x;
      const y = event.clientY - rect.top + scrollOffset.y;

      if (y < HEADER_HEIGHT) return; // Clicked on header

      const col = Math.floor((x - 60) / COLUMN_WIDTH);
      const row = Math.floor((y - HEADER_HEIGHT) / ROW_HEIGHT);

      if (col >= 0 && col < cols && row >= 0 && row < rows) {
        if (event.detail === 2) {
          handleCellDoubleClick(row, col);
        } else {
          handleCellClick(row, col);
        }
      }
    },
    [cols, rows, scrollOffset, handleCellClick, handleCellDoubleClick]
  );

  // Render grid to canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    // Draw column headers
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, width, HEADER_HEIGHT);
    ctx.strokeStyle = '#d0d0d0';
    ctx.lineWidth = 1;

    ctx.fillStyle = '#000000';
    ctx.font = '12px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let col = 0; col < cols; col++) {
      const x = 60 + col * COLUMN_WIDTH - scrollOffset.x;
      if (x + COLUMN_WIDTH < 60 || x > width) continue;

      ctx.fillText(getColumnLabel(col), x + COLUMN_WIDTH / 2, HEADER_HEIGHT / 2);
      ctx.beginPath();
      ctx.moveTo(x + COLUMN_WIDTH, 0);
      ctx.lineTo(x + COLUMN_WIDTH, HEADER_HEIGHT);
      ctx.stroke();
    }

    // Draw row numbers
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, 60, height);

    for (let row = 0; row < rows; row++) {
      const y = HEADER_HEIGHT + row * ROW_HEIGHT - scrollOffset.y;
      if (y + ROW_HEIGHT < HEADER_HEIGHT || y > height) continue;

      ctx.fillText(`${row + 1}`, 30, y + ROW_HEIGHT / 2);
      ctx.beginPath();
      ctx.moveTo(0, y + ROW_HEIGHT);
      ctx.lineTo(60, y + ROW_HEIGHT);
      ctx.stroke();
    }

    // Draw grid lines and cells
    ctx.textAlign = 'left';
    ctx.font = '13px sans-serif';

    for (let row = 0; row < rows; row++) {
      const y = HEADER_HEIGHT + row * ROW_HEIGHT - scrollOffset.y;
      if (y + ROW_HEIGHT < HEADER_HEIGHT || y > height) continue;

      for (let col = 0; col < cols; col++) {
        const x = 60 + col * COLUMN_WIDTH - scrollOffset.x;
        if (x + COLUMN_WIDTH < 60 || x > width) continue;

        const cellId = getCellId(row, col);
        const value = getCellValue(cellId);

        // Highlight selected cell
        if (selectedCell && selectedCell.row === row && selectedCell.col === col) {
          ctx.fillStyle = '#e3f2fd';
          ctx.fillRect(x, y, COLUMN_WIDTH, ROW_HEIGHT);
        }

        // Draw cell border
        ctx.strokeStyle = '#e0e0e0';
        ctx.strokeRect(x, y, COLUMN_WIDTH, ROW_HEIGHT);

        // Draw cell value
        ctx.fillStyle = '#000000';
        const displayValue = String(value ?? '');
        ctx.fillText(displayValue.slice(0, 15), x + 4, y + ROW_HEIGHT / 2 + 1);
      }
    }

    // Draw editing overlay if active
    if (editingCell) {
      const x = 60 + editingCell.col * COLUMN_WIDTH - scrollOffset.x;
      const y = HEADER_HEIGHT + editingCell.row * ROW_HEIGHT - scrollOffset.y;

      ctx.fillStyle = '#ffffff';
      ctx.fillRect(x, y, COLUMN_WIDTH, ROW_HEIGHT);
      ctx.strokeStyle = '#2196f3';
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, COLUMN_WIDTH, ROW_HEIGHT);
    }
  }, [
    cols,
    rows,
    selectedCell,
    editingCell,
    scrollOffset,
    cells,
    getCellValue,
  ]);

  return (
    <section className={`grid-panel ${className}`} aria-label="Data grid">
      <header className="grid-header">
        <h3>Grid</h3>
        <div className="grid-formula-bar">
          <label>
            <span className="grid-cell-ref">
              {selectedCell ? getCellId(selectedCell.row, selectedCell.col) : '—'}
            </span>
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleEditKeyDown}
              onFocus={() => {
                if (selectedCell) {
                  setEditingCell(selectedCell);
                  const cellId = getCellId(selectedCell.row, selectedCell.col);
                  setEditValue(getCellFormula(cellId) || '');
                }
              }}
              placeholder="Enter formula (e.g., =A1+B2 or =LIVE('metric_name'))"
            />
          </label>
        </div>
      </header>
      <div className="grid-canvas-container">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          onClick={handleCanvasClick}
          style={{ cursor: 'cell' }}
        />
        {editingCell && (
          <input
            autoFocus
            type="text"
            className="grid-cell-editor"
            style={{
              position: 'absolute',
              left: `${60 + editingCell.col * COLUMN_WIDTH - scrollOffset.x}px`,
              top: `${HEADER_HEIGHT + editingCell.row * ROW_HEIGHT - scrollOffset.y}px`,
              width: `${COLUMN_WIDTH}px`,
              height: `${ROW_HEIGHT}px`,
            }}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleEditKeyDown}
            onBlur={() => {
              const cellId = getCellId(editingCell.row, editingCell.col);
              setCellFormula(cellId, editValue);
              setEditingCell(null);
            }}
          />
        )}
      </div>
    </section>
  );
}
