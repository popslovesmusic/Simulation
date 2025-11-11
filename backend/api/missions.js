const express = require('express');
const { nanoid } = require('nanoid');

function createMissionRouter({ runningSimulations, launchSimulation, stopSimulation }) {
  const router = express.Router();

  router.get('/missions', (_req, res) => {
    const missions = Array.from(runningSimulations.values()).map((mission) => ({
      id: mission.id,
      name: mission.name,
      engine: mission.engine,
      status: mission.status,
      created_at: mission.created_at
    }));
    res.json({ missions });
  });

  router.post('/missions', (req, res) => {
    const { name, engine, parameters, brief_markdown, brief_latex } = req.body ?? {};

    if (!name || !engine) {
      return res.status(400).json({ error: 'Mission name and engine are required' });
    }

    const id = `mission_${nanoid(10)}`;
    const mission = {
      id,
      name,
      engine,
      parameters: parameters ?? {},
      brief_markdown: brief_markdown ?? '',
      brief_latex: brief_latex ?? '',
      status: 'pending',
      created_at: new Date().toISOString()
    };

    runningSimulations.set(id, mission);

    // Return 202 Accepted immediately - launch happens asynchronously
    res.status(202).json(mission);

    // Launch asynchronously and update status
    launchSimulation(mission)
      .catch((error) => {
        console.error(`Failed to launch mission ${id}:`, error);
        mission.status = 'failed';
        mission.error = error.message;
        runningSimulations.set(id, mission);
      });
  });

  router.get('/missions/:id', (req, res) => {
    const mission = runningSimulations.get(req.params.id);
    if (!mission) {
      return res.status(404).json({ error: 'Mission not found' });
    }
    res.json(mission);
  });

  router.post('/missions/:id/commands', (req, res) => {
    const mission = runningSimulations.get(req.params.id);
    if (!mission) {
      return res.status(404).json({ error: 'Mission not found' });
    }

    const { command } = req.body ?? {};
    if (!command) {
      return res.status(400).json({ error: 'Command is required' });
    }

    switch (command) {
      case 'start':
        mission.status = 'running';
        launchSimulation(mission).catch((error) => {
          mission.status = 'failed';
          mission.error = error.message;
        });
        break;
      case 'pause':
        mission.status = 'paused';
        break;
      case 'resume':
        mission.status = 'running';
        break;
      case 'abort':
        mission.status = 'terminated';
        stopSimulation(mission.id);
        runningSimulations.delete(mission.id);
        break;
      default:
        return res.status(400).json({ error: `Unsupported command: ${command}` });
    }

    res.json(mission);
  });

  return router;
}

module.exports = {
  createMissionRouter
};
