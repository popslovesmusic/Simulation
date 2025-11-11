const express = require('express');
const { symbolicsRouter } = require('./symbolics');
const { tutorialsRouter } = require('./tutorials');
const { sessionsRouter } = require('./sessions');

function createPlaygroundRouter() {
  const router = express.Router();

  router.use('/symbolics', symbolicsRouter);
  router.use('/', tutorialsRouter);
  router.use('/sessions', sessionsRouter);

  return router;
}

module.exports = {
  createPlaygroundRouter,
};
