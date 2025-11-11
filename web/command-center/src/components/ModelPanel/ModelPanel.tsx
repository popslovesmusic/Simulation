import { useQuery } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import './ModelPanel.css';

interface ParameterDefinition {
  type: 'integer' | 'float' | 'string' | 'boolean' | 'select';
  default: string | number | boolean;
  range?: [number, number];
  options?: string[];
  description: string;
  units?: string;
  cellReference?: string; // For linking to Grid cells
}

interface EquationDefinition {
  name: string;
  latex: string;
  editable_terms?: string[];
}

interface BoundaryConditionDefinition {
  types: string[];
  default: string;
}

interface EngineDescription {
  engine: string;
  display_name: string;
  description: string;
  parameters: Record<string, ParameterDefinition>;
  equations?: EquationDefinition[];
  boundary_conditions?: BoundaryConditionDefinition;
  output_metrics?: string[];
}

interface ModelPanelProps {
  engineName: string | null;
  onParameterChange?: (params: Record<string, unknown>) => void;
  onCreateMission?: () => void;
  isCreating?: boolean;
}

async function fetchEngineDescription(engineName: string): Promise<EngineDescription> {
  const response = await fetch(`/api/engines/${engineName}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('command-center-token') ?? ''}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch engine description: ${response.statusText}`);
  }

  return response.json();
}

export function ModelPanel({ engineName, onParameterChange, onCreateMission, isCreating }: ModelPanelProps) {
  const { t } = useTranslation();
  const [parameters, setParameters] = useState<Record<string, unknown>>({});

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['engine-description', engineName],
    queryFn: () => (engineName ? fetchEngineDescription(engineName) : Promise.resolve(null)),
    enabled: Boolean(engineName),
  });

  const handleParameterChange = useCallback(
    (paramName: string, value: unknown) => {
      const newParams = {
        ...parameters,
        [paramName]: value,
      };
      setParameters(newParams);
      onParameterChange?.(newParams);
    },
    [parameters, onParameterChange]
  );

  const renderParameterInput = useCallback(
    (paramName: string, paramDef: ParameterDefinition) => {
      const value = parameters[paramName] ?? paramDef.default;

      switch (paramDef.type) {
        case 'integer':
        case 'float':
          return (
            <div key={paramName} className="model-param">
              <label>
                <span className="model-param-label">
                  {paramName}
                  {paramDef.units && <span className="model-param-units">({paramDef.units})</span>}
                </span>
                <input
                  type="number"
                  value={String(value)}
                  step={paramDef.type === 'float' ? 0.01 : 1}
                  min={paramDef.range?.[0]}
                  max={paramDef.range?.[1]}
                  onChange={(e) => {
                    const parsed =
                      paramDef.type === 'integer'
                        ? parseInt(e.target.value, 10)
                        : parseFloat(e.target.value);
                    handleParameterChange(paramName, parsed);
                  }}
                />
                <span className="model-param-description">{paramDef.description}</span>
                {paramDef.range && (
                  <span className="model-param-range">
                    Range: [{paramDef.range[0]}, {paramDef.range[1]}]
                  </span>
                )}
                {paramDef.cellReference && (
                  <span className="model-param-cell-ref">
                    Linked to: {paramDef.cellReference}
                  </span>
                )}
              </label>
            </div>
          );

        case 'boolean':
          return (
            <div key={paramName} className="model-param">
              <label>
                <span className="model-param-label">{paramName}</span>
                <input
                  type="checkbox"
                  checked={Boolean(value)}
                  onChange={(e) => handleParameterChange(paramName, e.target.checked)}
                />
                <span className="model-param-description">{paramDef.description}</span>
              </label>
            </div>
          );

        case 'select':
          return (
            <div key={paramName} className="model-param">
              <label>
                <span className="model-param-label">{paramName}</span>
                <select
                  value={String(value)}
                  onChange={(e) => handleParameterChange(paramName, e.target.value)}
                >
                  {paramDef.options?.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <span className="model-param-description">{paramDef.description}</span>
              </label>
            </div>
          );

        case 'string':
        default:
          return (
            <div key={paramName} className="model-param">
              <label>
                <span className="model-param-label">{paramName}</span>
                <input
                  type="text"
                  value={String(value)}
                  onChange={(e) => handleParameterChange(paramName, e.target.value)}
                />
                <span className="model-param-description">{paramDef.description}</span>
              </label>
            </div>
          );
      }
    },
    [parameters, handleParameterChange]
  );

  if (!engineName) {
    return (
      <section className="model-panel" aria-label="Engine configuration">
        <header className="panel-header">
          <h3>Model Configuration</h3>
        </header>
        <div className="panel-body">
          <p>Select an engine to configure parameters.</p>
        </div>
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="model-panel" aria-label="Engine configuration">
        <header className="panel-header">
          <h3>Model Configuration</h3>
        </header>
        <div className="panel-body">
          <p aria-live="polite">Loading engine description...</p>
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section className="model-panel" aria-label="Engine configuration">
        <header className="panel-header">
          <h3>Model Configuration</h3>
        </header>
        <div className="panel-body">
          <p role="alert">{(error as Error).message}</p>
        </div>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <section className="model-panel" aria-label="Engine configuration">
      <header className="panel-header">
        <h3>{data.display_name}</h3>
        <p className="model-description">{data.description}</p>
      </header>

      <div className="panel-body">
        {/* Parameters Section */}
        <section className="model-section">
          <h4>Parameters</h4>
          <div className="model-params-grid">
            {Object.entries(data.parameters).map(([name, def]) =>
              renderParameterInput(name, def)
            )}
          </div>
        </section>

        {/* Equations Section */}
        {data.equations && data.equations.length > 0 && (
          <section className="model-section">
            <h4>Governing Equations</h4>
            <div className="model-equations">
              {data.equations.map((eq) => (
                <div key={eq.name} className="model-equation">
                  <strong>{eq.name}:</strong>
                  <div className="model-equation-latex">
                    <code>{eq.latex}</code>
                  </div>
                  {eq.editable_terms && eq.editable_terms.length > 0 && (
                    <span className="model-equation-editable">
                      Editable terms: {eq.editable_terms.join(', ')}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Boundary Conditions Section */}
        {data.boundary_conditions && (
          <section className="model-section">
            <h4>Boundary Conditions</h4>
            <div className="model-param">
              <label>
                <span className="model-param-label">Type</span>
                <select
                  value={
                    (parameters.boundary_condition as string) ??
                    data.boundary_conditions.default
                  }
                  onChange={(e) => handleParameterChange('boundary_condition', e.target.value)}
                >
                  {data.boundary_conditions.types.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </section>
        )}

        {/* Output Metrics Section */}
        {data.output_metrics && data.output_metrics.length > 0 && (
          <section className="model-section">
            <h4>Output Metrics</h4>
            <div className="model-metrics">
              <ul>
                {data.output_metrics.map((metric) => (
                  <li key={metric}>
                    <code>{metric}</code>
                  </li>
                ))}
              </ul>
              <p className="model-metrics-hint">
                Use <code>=LIVE("metric_name")</code> in the Grid to stream real-time values.
              </p>
            </div>
          </section>
        )}

        {/* Create Mission Button */}
        <div className="model-actions">
          <button
            type="button"
            className="primary"
            onClick={onCreateMission}
            disabled={!onCreateMission || isCreating}
          >
            {isCreating ? 'Creating Mission...' : 'Create Mission with Configuration'}
          </button>
        </div>
      </div>
    </section>
  );
}
