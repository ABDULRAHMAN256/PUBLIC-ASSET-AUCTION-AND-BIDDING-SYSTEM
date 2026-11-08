const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-me';

function signToken(user) {
  return jwt.sign({ id: user.user_id, role: user.role }, JWT_SECRET, { expiresIn: '7d' });
}

function verifyJWT(req, res, next) {
  const header = req.headers.authorization || '';
  if (!header.startsWith('Bearer ')) return res.status(401).json({ error: 'missing_token' });
  try {
    const payload = jwt.verify(header.slice(7), JWT_SECRET);
    req.user = { id: payload.id, role: payload.role };
    next();
  } catch (err) {
    res.status(401).json({ error: 'invalid_token' });
  }
}

function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user) return res.status(401).json({ error: 'missing_token' });
    if (!roles.includes(req.user.role)) return res.status(403).json({ error: 'forbidden' });
    next();
  };
}

module.exports = { signToken, verifyJWT, requireRole };
