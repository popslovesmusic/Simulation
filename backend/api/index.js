const { createMissionRouter } = require('./missions');
const { createPlaygroundRouter } = require('./playground');
const { authenticateRequest, registry } = require('./auth');

function configureApi(app, context) {
  const router = createMissionRouter(context);
  app.use('/api', authenticateRequest, router);
  app.use('/api/playground', authenticateRequest, createPlaygroundRouter());

  return {
    tokens: registry.getAll()
  };
}

module.exports = {
  configureApi
};
