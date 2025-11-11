import { useState, useCallback, useEffect, useRef } from 'react';

interface Cell {
  formula: string;
  value: string | number | null;
  dependencies: string[];
  isLive: boolean;
  liveMetric?: string;
}

type CellMap = Map<string, Cell>;

function parseCellReferences(formula: string): string[] {
  const cellRefRegex = /\b([A-Z]+\d+)\b/g;
  const matches = formula.match(cellRefRegex);
  return matches ? Array.from(new Set(matches)) : [];
}

function parseLiveFunction(formula: string): string | null {
  const liveMatch = formula.match(/LIVE\s*\(\s*['"]([^'"]+)['"]\s*\)/i);
  return liveMatch ? liveMatch[1] : null;
}

function evaluateFormula(
  formula: string,
  getCellValueFn: (cellId: string) => string | number | null
): string | number | null {
  try {
    // Check for LIVE() function
    const liveMetric = parseLiveFunction(formula);
    if (liveMetric) {
      return `=LIVE("${liveMetric}")`; // Return placeholder until WebSocket updates it
    }

    // Replace cell references with their values
    let expression = formula;
    const cellRefs = parseCellReferences(formula);

    for (const ref of cellRefs) {
      const value = getCellValueFn(ref);
      if (value === null || value === undefined) {
        return null;
      }
      // Replace cell reference with its numeric value
      expression = expression.replace(new RegExp(`\\b${ref}\\b`, 'g'), String(value));
    }

    // Support basic arithmetic and math functions
    const mathContext: Record<string, number | ((x: number) => number)> = {
      PI: Math.PI,
      E: Math.E,
      sin: Math.sin,
      cos: Math.cos,
      tan: Math.tan,
      sqrt: Math.sqrt,
      abs: Math.abs,
      floor: Math.floor,
      ceil: Math.ceil,
      round: Math.round,
      max: Math.max,
      min: Math.min,
    };

    // Create safe evaluation function
    const func = new Function(...Object.keys(mathContext), `return ${expression}`);
    const result = func(...Object.values(mathContext));

    return typeof result === 'number' ? result : String(result);
  } catch (error) {
    return `#ERROR: ${error instanceof Error ? error.message : 'Invalid formula'}`;
  }
}

export function useGridEngine(rows: number, cols: number) {
  const [cells, setCells] = useState<CellMap>(new Map());
  const liveMetricsRef = useRef<Map<string, Set<string>>>(new Map()); // metric -> cell IDs
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for LIVE() metrics
  useEffect(() => {
    const ws = new WebSocket(`${window.location.origin.replace('http', 'ws')}/ws/metrics`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Grid WebSocket connected for LIVE() metrics');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'metrics:update' && message.data) {
          const { name, value } = message.data;

          // Update all cells that use this metric
          const subscribedCells = liveMetricsRef.current.get(name);
          if (subscribedCells) {
            setCells((prevCells) => {
              const newCells = new Map(prevCells);
              subscribedCells.forEach((cellId) => {
                const cell = newCells.get(cellId);
                if (cell && cell.isLive) {
                  newCells.set(cellId, {
                    ...cell,
                    value: value,
                  });
                }
              });
              return newCells;
            });
          }
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Grid WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Grid WebSocket closed');
    };

    return () => {
      ws.close();
    };
  }, []);

  const getCellValue = useCallback(
    (cellId: string): string | number | null => {
      const cell = cells.get(cellId);
      return cell?.value ?? null;
    },
    [cells]
  );

  const getCellFormula = useCallback(
    (cellId: string): string | null => {
      const cell = cells.get(cellId);
      return cell?.formula ?? null;
    },
    [cells]
  );

  const subscribeLiveMetric = useCallback((cellId: string, metricName: string) => {
    const subscribers = liveMetricsRef.current.get(metricName) || new Set();
    subscribers.add(cellId);
    liveMetricsRef.current.set(metricName, subscribers);
  }, []);

  const unsubscribeLiveMetric = useCallback((cellId: string, metricName: string) => {
    const subscribers = liveMetricsRef.current.get(metricName);
    if (subscribers) {
      subscribers.delete(cellId);
      if (subscribers.size === 0) {
        liveMetricsRef.current.delete(metricName);
      }
    }
  }, []);

  const evaluateCell = useCallback(
    (cellId: string): void => {
      setCells((prevCells) => {
        const cell = prevCells.get(cellId);
        if (!cell) return prevCells;

        const value = evaluateFormula(cell.formula, (id) => {
          const targetCell = prevCells.get(id);
          return targetCell?.value ?? null;
        });

        const newCells = new Map(prevCells);
        newCells.set(cellId, { ...cell, value });
        return newCells;
      });
    },
    []
  );

  const setCellFormula = useCallback(
    (cellId: string, formula: string): void => {
      setCells((prevCells) => {
        const newCells = new Map(prevCells);
        const prevCell = prevCells.get(cellId);

        // Unsubscribe from previous LIVE metric
        if (prevCell?.isLive && prevCell.liveMetric) {
          unsubscribeLiveMetric(cellId, prevCell.liveMetric);
        }

        const cleanFormula = formula.trim();

        // Handle empty formula
        if (!cleanFormula) {
          newCells.delete(cellId);
          return newCells;
        }

        // Check if formula starts with =
        if (!cleanFormula.startsWith('=')) {
          // Plain value
          newCells.set(cellId, {
            formula: cleanFormula,
            value: cleanFormula,
            dependencies: [],
            isLive: false,
          });
          return newCells;
        }

        const formulaBody = cleanFormula.substring(1); // Remove =
        const dependencies = parseCellReferences(formulaBody);
        const liveMetric = parseLiveFunction(formulaBody);

        // Create cell
        const cell: Cell = {
          formula: cleanFormula,
          value: null,
          dependencies,
          isLive: !!liveMetric,
          liveMetric: liveMetric ?? undefined,
        };

        // Subscribe to LIVE metric if present
        if (liveMetric) {
          subscribeLiveMetric(cellId, liveMetric);
          cell.value = `=LIVE("${liveMetric}")`; // Placeholder
        } else {
          // Evaluate formula immediately
          cell.value = evaluateFormula(formulaBody, (id) => {
            const targetCell = prevCells.get(id);
            return targetCell?.value ?? null;
          });
        }

        newCells.set(cellId, cell);

        // Re-evaluate dependent cells
        const cellsToUpdate = new Set<string>();
        for (const [id, c] of newCells.entries()) {
          if (c.dependencies.includes(cellId)) {
            cellsToUpdate.add(id);
          }
        }

        cellsToUpdate.forEach((id) => {
          const c = newCells.get(id);
          if (c && !c.isLive) {
            const value = evaluateFormula(c.formula.substring(1), (targetId) => {
              const targetCell = newCells.get(targetId);
              return targetCell?.value ?? null;
            });
            newCells.set(id, { ...c, value });
          }
        });

        return newCells;
      });
    },
    [subscribeLiveMetric, unsubscribeLiveMetric]
  );

  return {
    cells,
    getCellValue,
    getCellFormula,
    setCellFormula,
    evaluateCell,
    subscribeLiveMetric,
    unsubscribeLiveMetric,
  };
}
