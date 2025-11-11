import { FormEvent, useState } from 'react';
import { useSymbolicSandbox } from './useSymbolicSandbox';

function VariablesEditor({
  variables,
  onChange,
  onRemove,
  onAdd,
}: {
  variables: Record<string, number>;
  onChange: (name: string, value: number) => void;
  onRemove: (name: string) => void;
  onAdd: (name: string) => void;
}) {
  const [draftName, setDraftName] = useState('');

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onAdd(draftName);
    setDraftName('');
  };

  return (
    <div className="symbolics-variables">
      <h4>Variables</h4>
      <ul>
        {Object.entries(variables).map(([name, value]) => (
          <li key={name}>
            <label>
              <span>{name}</span>
              <input
                aria-label={`Value for ${name}`}
                type="number"
                step="any"
                value={value}
                onChange={(event) => onChange(name, Number(event.target.value))}
              />
            </label>
            <button type="button" onClick={() => onRemove(name)} aria-label={`Remove ${name}`}>
              ×
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={handleSubmit} className="symbolics-add-variable">
        <input
          type="text"
          placeholder="Add variable"
          value={draftName}
          onChange={(event) => setDraftName(event.target.value)}
        />
        <button type="submit">Add</button>
      </form>
    </div>
  );
}

export function SymbolicsPanel() {
  const {
    context,
    expression,
    setExpression,
    operations,
    toggleOperation,
    variables,
    setVariableValue,
    removeVariable,
    addVariable,
    result,
    error,
    loading,
    evaluate,
  } = useSymbolicSandbox();

  return (
    <section className="playground-panel" aria-label="Symbolics Sandbox">
      <header className="panel-header">
        <h3>Symbolics Sandbox</h3>
        <p>Experiment with SymPy-backed expressions before mission execution.</p>
      </header>
      <div className="panel-body">
        <label className="symbolics-expression">
          <span>Expression</span>
          <textarea
            value={expression}
            rows={4}
            onChange={(event) => setExpression(event.target.value)}
            placeholder="Enter a SymPy-compatible expression"
          />
        </label>
        <div className="symbolics-controls">
          <fieldset>
            <legend>Operations</legend>
            {(context?.operations ?? operations).map((operation) => (
              <label key={operation}>
                <input
                  type="checkbox"
                  checked={operations.includes(operation)}
                  onChange={() => toggleOperation(operation)}
                />
                {operation}
              </label>
            ))}
          </fieldset>
          <VariablesEditor
            variables={variables}
            onChange={setVariableValue}
            onRemove={removeVariable}
            onAdd={addVariable}
          />
        </div>
        <div className="symbolics-actions">
          <button type="button" onClick={evaluate} disabled={loading}>
            {loading ? 'Evaluating…' : 'Evaluate'}
          </button>
        </div>
        {error && <p className="symbolics-error">{error}</p>}
        {result && (
          <div className="symbolics-result" aria-live="polite">
            <h4>Result</h4>
            <dl>
              {result.result?.simplified && (
                <>
                  <dt>Simplified</dt>
                  <dd>{result.result.simplified.text}</dd>
                </>
              )}
              {result.result?.numeric !== undefined && (
                <>
                  <dt>Numeric</dt>
                  <dd>{String(result.result.numeric)}</dd>
                </>
              )}
              {result.result?.derivative && (
                <>
                  <dt>Derivative</dt>
                  <dd>{result.result.derivative.text}</dd>
                </>
              )}
              {result.result?.integral && (
                <>
                  <dt>Integral</dt>
                  <dd>{result.result.integral.text}</dd>
                </>
              )}
            </dl>
            <details>
              <summary>SymPy representation</summary>
              <pre>{result.result?.repr}</pre>
            </details>
          </div>
        )}
        {context && (
          <aside className="symbolics-hints">
            <h4>Hints</h4>
            <p>Available functions: {context.functions.join(', ')}</p>
            <p>Examples:</p>
            <ul>
              {context.examples.map((example) => (
                <li key={example}>{example}</li>
              ))}
            </ul>
          </aside>
        )}
      </div>
    </section>
  );
}
