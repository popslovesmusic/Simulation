import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  SymbolicContext,
  SymbolicEvaluationRequest,
  SymbolicEvaluationResponse,
  apiClient,
} from '../../services/apiClient';

type VariableMap = Record<string, number>;

type SandboxState = {
  expression: string;
  variables: VariableMap;
  operations: string[];
  assumptions: Record<string, Record<string, boolean>>;
};

const DEFAULT_STATE: SandboxState = {
  expression: 'sin(x)**2 + cos(x)**2',
  variables: { x: 0 },
  operations: ['simplify', 'evalf'],
  assumptions: { x: { real: true } },
};

export function useSymbolicSandbox(initialState: Partial<SandboxState> = {}) {
  const [context, setContext] = useState<SymbolicContext | null>(null);
  const [state, setState] = useState<SandboxState>({
    ...DEFAULT_STATE,
    ...initialState,
    variables: { ...DEFAULT_STATE.variables, ...(initialState.variables ?? {}) },
    assumptions: { ...DEFAULT_STATE.assumptions, ...(initialState.assumptions ?? {}) },
    operations: initialState.operations ?? DEFAULT_STATE.operations,
  });
  const [result, setResult] = useState<SymbolicEvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .getSymbolicContext()
      .then((data) => {
        if (!cancelled) {
          setContext(data);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const evaluate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: SymbolicEvaluationRequest = {
        expression: state.expression,
        variables: state.variables,
        operations: state.operations,
        assumptions: state.assumptions,
      };
      const response = await apiClient.evaluateSymbolicExpression(payload);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [state]);

  const toggleOperation = useCallback((operation: string) => {
    setState((prev) => {
      const hasOp = prev.operations.includes(operation);
      const operations = hasOp
        ? prev.operations.filter((op) => op !== operation)
        : [...prev.operations, operation];
      return { ...prev, operations };
    });
  }, []);

  const setExpression = useCallback((expression: string) => {
    setState((prev) => ({ ...prev, expression }));
  }, []);

  const setVariableValue = useCallback((name: string, value: number) => {
    setState((prev) => ({
      ...prev,
      variables: {
        ...prev.variables,
        [name]: value,
      },
    }));
  }, []);

  const removeVariable = useCallback((name: string) => {
    setState((prev) => {
      const next = { ...prev.variables };
      delete next[name];
      return { ...prev, variables: next };
    });
  }, []);

  const addVariable = useCallback((name: string) => {
    const sanitized = name.trim();
    if (!sanitized) return;
    setState((prev) => ({
      ...prev,
      variables: {
        ...prev.variables,
        [sanitized]: prev.variables[sanitized] ?? 0,
      },
    }));
  }, []);

  const contextVariables = useMemo(() => Object.keys(state.variables), [state.variables]);

  return {
    context,
    state,
    expression: state.expression,
    operations: state.operations,
    variables: state.variables,
    assumptions: state.assumptions,
    result,
    error,
    loading,
    evaluate,
    toggleOperation,
    setExpression,
    setVariableValue,
    removeVariable,
    addVariable,
    contextVariables,
  };
}
