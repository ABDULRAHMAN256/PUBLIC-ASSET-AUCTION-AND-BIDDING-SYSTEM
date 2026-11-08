// routes/assets.js
const express = require('express');
const db = require('../db');
const { verifyJWT, requireRole } = require('../middleware/auth');

const router = express.Router();

// -------------------------------------------------------------
// GET /api/assets?category=&search=&status=
// -------------------------------------------------------------
router.get('/', verifyJWT, (req, res) => {
  const { category, search, status } = req.query;

  const where = [];
  const params = [];

  if (category) {
    if (/^\d+$/.test(category)) {
      where.push('a.category_id = ?');
      params.push(Number(category));
    } else {
      where.push('c.name = ?');
      params.push(category);
    }
  }
  if (search) {
    where.push('(a.title LIKE ? OR a.description LIKE ?)');
    params.push(`%${search}%`, `%${search}%`);
  }
  if (status && ['upcoming', 'live', 'sold', 'cancelled'].includes(status)) {
    where.push('a.status = ?');
    params.push(status);
  }

  const sql = `
    SELECT a.*, c.name AS category_name, u.username AS seller_username
    FROM assets a
    JOIN categories c ON c.category_id = a.category_id
    JOIN users u      ON u.user_id     = a.seller_id
    ${where.length ? 'WHERE ' + where.join(' AND ') : ''}
    ORDER BY a.created_at DESC
  `;
  const rows = db.prepare(sql).all(...params);
  res.status(200).json(rows);
});

// -------------------------------------------------------------
// GET /api/assets/:id
// -------------------------------------------------------------
router.get('/:id', verifyJWT, (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id)) return res.status(400).json({ error: 'invalid_id' });

  const asset = db.prepare(`
    SELECT a.*, c.name AS category_name, u.username AS seller_username
    FROM assets a
    JOIN categories c ON c.category_id = a.category_id
    JOIN users u      ON u.user_id     = a.seller_id
    WHERE a.asset_id = ?
  `).get(id);
  if (!asset) return res.status(404).json({ error: 'not_found' });

  const images = db.prepare(
    'SELECT image_id, file_path, is_primary FROM asset_images WHERE asset_id = ?'
  ).all(id);

  res.status(200).json({ asset, images });
});

// -------------------------------------------------------------
// POST /api/assets   (Seller only)
// -------------------------------------------------------------
router.post('/', verifyJWT, requireRole('seller', 'admin'), (req, res) => {
  const {
    category_id, title, description,
    starting_price, reserve_price, min_increment,
    start_time, end_time, images
  } = req.body || {};

  if (!title || typeof title !== 'string' || title.trim().length < 3) {
    return res.status(400).json({ error: 'title_invalid' });
  }
  if (!Number.isFinite(starting_price) || starting_price <= 0) {
    return res.status(400).json({ error: 'starting_price_invalid' });
  }
  if (!Number.isFinite(reserve_price) || reserve_price < starting_price) {
    return res.status(400).json({ error: 'reserve_price_invalid' });
  }
  if (!Number.isFinite(min_increment) || min_increment <= 0) {
    return res.status(400).json({ error: 'min_increment_invalid' });
  }
  if (!start_time || !end_time) {
    return res.status(400).json({ error: 'times_required' });
  }
  if (new Date(end_time) <= new Date(start_time)) {
    return res.status(400).json({ error: 'end_time_must_be_after_start_time' });
  }
  const cat = db.prepare('SELECT 1 FROM categories WHERE category_id = ?').get(Number(category_id));
  if (!cat) return res.status(400).json({ error: 'category_not_found' });

  const insertAsset = db.prepare(`
    INSERT INTO assets (seller_id, category_id, title, description,
                        starting_price, reserve_price, min_increment,
                        current_price, status, start_time, end_time, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'upcoming', ?, ?, ?)
  `);
  const insertImage = db.prepare(
    'INSERT INTO asset_images (asset_id, file_path, is_primary) VALUES (?, ?, ?)'
  );

  const tx = db.transaction(() => {
    const info = insertAsset.run(
      req.user.id,
      Number(category_id), title.trim(), description || '',
      starting_price, reserve_price, min_increment,
      starting_price,
      start_time, end_time, new Date().toISOString()
    );
    const assetId = info.lastInsertRowid;

    if (Array.isArray(images)) {
      images.slice(0, 5).forEach((url, i) => {
        if (typeof url === 'string' && url.trim()) {
          insertImage.run(assetId, url.trim(), i === 0 ? 1 : 0);
        }
      });
    }
    return assetId;
  });

  let assetId;
  try {
    assetId = tx();
  } catch (err) {
    console.error('[assets.create]', err);
    return res.status(500).json({ error: 'server_error' });
  }
  res.status(201).json({ asset_id: assetId });
});

// -------------------------------------------------------------
// PUT /api/assets/:id
// -------------------------------------------------------------
router.put('/:id', verifyJWT, requireRole('seller', 'admin'), (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id)) return res.status(400).json({ error: 'invalid_id' });

  const asset = db.prepare('SELECT seller_id, status FROM assets WHERE asset_id = ?').get(id);
  if (!asset) return res.status(404).json({ error: 'not_found' });

  if (req.user.role !== 'admin' && asset.seller_id !== req.user.id) {
    return res.status(403).json({ error: 'not_owner' });
  }
  if (asset.status === 'sold') {
    return res.status(400).json({ error: 'sold_assets_are_immutable' });
  }

  const allowed = ['title', 'description', 'reserve_price', 'min_increment', 'end_time'];
  const updates = [];
  const params = [];
  for (const key of allowed) {
    if (req.body[key] !== undefined) {
      updates.push(`${key} = ?`);
      params.push(req.body[key]);
    }
  }
  if (updates.length === 0) return res.status(400).json({ error: 'no_fields' });
  params.push(id);

  db.prepare(`UPDATE assets SET ${updates.join(', ')} WHERE asset_id = ?`).run(...params);
  res.status(200).json({ updated: true });
});

// -------------------------------------------------------------
// DELETE /api/assets/:id
// -------------------------------------------------------------
router.delete('/:id', verifyJWT, requireRole('seller', 'admin'), (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id)) return res.status(400).json({ error: 'invalid_id' });

  const asset = db.prepare('SELECT seller_id, status FROM assets WHERE asset_id = ?').get(id);
  if (!asset) return res.status(404).json({ error: 'not_found' });

  if (req.user.role !== 'admin' && asset.seller_id !== req.user.id) {
    return res.status(403).json({ error: 'not_owner' });
  }
  if (asset.status === 'live') {
    return res.status(409).json({ error: 'cannot_delete_live_asset' });
  }

  db.prepare('DELETE FROM assets WHERE asset_id = ?').run(id);
  res.status(200).json({ deleted: true });
});

module.exports = router;
