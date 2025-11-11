const { createMissionRouter } = require('./missions');
const { authenticateRequest, registry } = require('./auth');

function configureApi(app, context) {
  const router = createMissionRouter(context);
  app.use('/api', authenticateRequest, router);

  return {
    tokens: registry.getAll()
  };
}

module.exports = {
  configureApi
};
