const express = require('express');
const { runPythonTool } = require('./pythonBridge');

const ALLOWED_OPERATIONS = ['simplify', 'evalf', 'diff', 'integrate'];

const router = express.Router();

router.post('/evaluate', async (req, res) => {
  const { expression, variables = {}, operations = ['simplify', 'evalf'], assumptions = {} } = req.body || {};

  if (!expression || typeof expression !== 'string') {
    res.status(400).json({ error: 'expression is required' });
    return;
  }

  const sanitizedOperations = Array.isArray(operations)
    ? operations.filter((op) => ALLOWED_OPERATIONS.includes(op))
    : ['simplify', 'evalf'];

  try {
    const response = await runPythonTool('symbolic_eval.py', [], {
      expression,
      variables,
      operations: sanitizedOperations,
      assumptions,
    });

    if (response.status !== 'ok') {
      res.status(422).json({ error: response.error || 'Symbolic evaluation failed' });
      return;
    }

    res.json({
      ...response,
      availableOperations: ALLOWED_OPERATIONS,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/context', (_req, res) => {
  res.json({
    functions: ['sin', 'cos', 'tan', 'sqrt', 'log', 'exp', 'diff', 'integrate', 'simplify', 'factor', 'expand'],
    constants: ['pi', 'E'],
    operations: ALLOWED_OPERATIONS,
    examples: [
      'sin(x)**2 + cos(x)**2',
      'diff(exp(x) * cos(y), x)',
      'integrate(sin(x)/x, (x, 0, pi))',
    ],
  });
});

module.exports = { symbolicsRouter: router };
