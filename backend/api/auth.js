const crypto = require('crypto');

class TokenRegistry {
  constructor(seedTokens = []) {
    this.tokens = new Set(seedTokens.filter(Boolean));
    if (this.tokens.size === 0) {
      this.tokens.add(crypto.randomBytes(32).toString('hex'));
    }
  }

  getAll() {
    return Array.from(this.tokens);
  }

  validate(token) {
    return token && this.tokens.has(token);
  }
}

const registry = new TokenRegistry([process.env.DASE_API_TOKEN]);

function authenticateRequest(req, res, next) {
  const header = req.get('Authorization');
  if (!header) {
    return res.status(401).json({ error: 'Missing Authorization header' });
  }

  const match = header.match(/^Bearer (.+)$/);
  if (!match) {
    return res.status(401).json({ error: 'Invalid Authorization header format' });
  }

  const token = match[1];
  if (!registry.validate(token)) {
    return res.status(403).json({ error: 'Invalid API token' });
  }

  return next();
}

module.exports = {
  authenticateRequest,
  registry
};
