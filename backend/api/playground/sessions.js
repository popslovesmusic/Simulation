const express = require('express');
const { runPythonTool } = require('./pythonBridge');

const router = express.Router();

router.get('/', async (_req, res) => {
  try {
    const response = await runPythonTool('session_store.py', ['list']);
    if (response.status !== 'ok') {
      res.status(500).json({ error: response.error || 'Failed to load sessions' });
      return;
    }
    res.json({ sessions: response.sessions || [] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/:sessionId', async (req, res) => {
  try {
    const response = await runPythonTool('session_store.py', ['get', req.params.sessionId]);
    if (response.status !== 'ok') {
      res.status(404).json({ error: response.error || 'Session not found' });
      return;
    }
    res.json(response.session);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/:sessionId', async (req, res) => {
  try {
    const response = await runPythonTool('session_store.py', ['save', req.params.sessionId], req.body || {});
    if (response.status !== 'ok') {
      res.status(422).json({ error: response.error || 'Failed to persist session' });
      return;
    }
    res.json(response.session);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/:sessionId/notes', async (req, res) => {
  try {
    const response = await runPythonTool('session_store.py', ['note', req.params.sessionId], req.body || {});
    if (response.status !== 'ok') {
      res.status(422).json({ error: response.error || 'Failed to append note' });
      return;
    }
    res.json(response.note);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = { sessionsRouter: router };
