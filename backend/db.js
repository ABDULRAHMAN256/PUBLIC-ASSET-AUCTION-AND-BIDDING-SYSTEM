const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const DB_PATH = path.join(__dirname, 'auction.db');
const db = new Database(DB_PATH);

db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
db.pragma('busy_timeout = 5000');

const hasSchema = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").get();
if (!hasSchema) {
  const sql = fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8');
  db.exec(sql);
  console.log('[db] schema.sql applied');
}

module.exports = db;
