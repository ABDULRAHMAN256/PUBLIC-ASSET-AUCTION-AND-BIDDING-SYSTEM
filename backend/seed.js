const bcrypt = require('bcryptjs');
const db = require('./db');
const now = () => new Date().toISOString();

if (db.prepare("SELECT COUNT(*) AS c FROM users").get().c > 0) {
  console.log('[seed] Users exist. Delete auction.db to reseed.');
  process.exit(0);
}

const insertUser = db.prepare("INSERT INTO users (username, email, password_hash, full_name, phone, role, kyc_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
const insertCat = db.prepare("INSERT INTO categories (name) VALUES (?)");
const insertAsset = db.prepare("INSERT INTO assets (seller_id, category_id, title, description, starting_price, reserve_price, min_increment, current_price, status, start_time, end_time, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
const insertImage = db.prepare("INSERT INTO asset_images (asset_id, file_path, is_primary) VALUES (?, ?, ?)");
const hash = (pw) => bcrypt.hashSync(pw, 10);

insertCat.run('Vehicles');
insertCat.run('Real Estate');
insertCat.run('Equipment');

insertUser.run('admin', 'admin@upauction.ug', hash('admin123'), 'System Admin', '+256700000000', 'admin', 'approved', now());
insertUser.run('seller_mot', 's1@upauction.ug', hash('seller123'), 'Ministry of Transport', '+256711111111', 'seller', 'approved', now());
insertUser.run('seller_lands', 's2@upauction.ug', hash('seller123'), 'Lands Commission', '+256722222222', 'seller', 'approved', now());
insertUser.run('bidder_john', 'john@upauction.ug', hash('bidder123'), 'John Doe', '+256733333333', 'bidder', 'approved', now());

const s1 = db.prepare("SELECT user_id FROM users WHERE username = 'seller_mot'").get().user_id;
const s2 = db.prepare("SELECT user_id FROM users WHERE username = 'seller_lands'").get().user_id;
const cVeh = db.prepare("SELECT category_id FROM categories WHERE name = 'Vehicles'").get().category_id;
const cProp = db.prepare("SELECT category_id FROM categories WHERE name = 'Real Estate'").get().category_id;
const cEq = db.prepare("SELECT category_id FROM categories WHERE name = 'Equipment'").get().category_id;

const isoOffset = ({ days = 0, hours = 0 } = {}) => {
  const d = new Date(); d.setDate(d.getDate() + days); d.setHours(d.getHours() + hours); return d.toISOString();
};

insertAsset.run(s1, cVeh, 'Toyota Land Cruiser V8', 'Ex-Ministry.', 45000000.00, 60000000.00, 500000.00, 45000000.00, 'live', isoOffset({ days: -1 }), isoOffset({ days: 2 }), now());
insertAsset.run(s2, cProp, 'Plot 0.5 Acres Kololo', 'Freehold title.', 800000000.00, 900000000.00, 10000000.00, 800000000.00, 'upcoming', isoOffset({ days: 3 }), isoOffset({ days: 10 }), now());
insertAsset.run(s1, cEq, 'JCB 3CX Backhoe', 'Ex-UNRA.', 120000000.00, 150000000.00, 1000000.00, 120000000.00, 'live', isoOffset({ days: -2 }), isoOffset({ hours: 6 }), now());

console.log('Seed complete. Matches ERD exactly.');
