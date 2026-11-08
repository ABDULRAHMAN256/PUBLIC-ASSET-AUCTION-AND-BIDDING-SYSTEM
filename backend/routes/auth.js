const express = require('express');
const bcrypt = require('bcryptjs');
const db = require('../db');
const { signToken } = require('../middleware/auth');
const router = express.Router();

router.post('/register', (req, res) => {
  const { username, email, password, full_name, phone } = req.body || {};
  if (!username || !email || !password) return res.status(400).json({ error: 'missing_fields' });

  const dup = db.prepare('SELECT 1 FROM users WHERE username = ? OR email = ? LIMIT 1').get(username, email);
  if (dup) return res.status(400).json({ error: 'duplicate_user' });

  const hash = bcrypt.hashSync(password, 10);
  const info = db.prepare("INSERT INTO users (username, email, password_hash, full_name, phone, role, kyc_status, created_at) VALUES (?, ?, ?, ?, ?, 'bidder', 'pending', ?)").run(username, email, hash, full_name || null, phone || null, new Date().toISOString());

  const token = signToken({ user_id: info.lastInsertRowid, role: 'bidder' });
  res.status(201).json({ token, user_id: info.lastInsertRowid });
});

router.post('/login', (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'missing_fields' });

  const row = db.prepare('SELECT * FROM users WHERE username = ? OR email = ? LIMIT 1').get(username, username);
  if (!row || !bcrypt.compareSync(password, row.password_hash)) {
    return res.status(401).json({ error: 'invalid_credentials' });
  }

  const token = signToken(row);
  res.status(200).json({ token });
});

module.exports = router;
