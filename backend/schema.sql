PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS deposits;
DROP TABLE IF EXISTS kyc_documents;
DROP TABLE IF EXISTS bids;
DROP TABLE IF EXISTS asset_images;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  username      VARCHAR(50) NOT NULL UNIQUE,
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name     VARCHAR(100),
  phone         VARCHAR(20),
  role          VARCHAR(10) NOT NULL CHECK(role IN ('bidder','seller','admin')) DEFAULT 'bidder',
  kyc_status    VARCHAR(10) NOT NULL DEFAULT 'pending',
  created_at    DATETIME NOT NULL
);

CREATE TABLE categories (
  category_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name        VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE assets (
  asset_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  seller_id      INTEGER NOT NULL REFERENCES users(user_id),
  category_id    INTEGER NOT NULL REFERENCES categories(category_id),
  title          VARCHAR(150) NOT NULL,
  description    TEXT,
  starting_price DECIMAL(12,2) NOT NULL,
  reserve_price  DECIMAL(12,2) NOT NULL,
  min_increment  DECIMAL(12,2) NOT NULL DEFAULT 500000.00,
  current_price  DECIMAL(12,2) NOT NULL,
  status         VARCHAR(10) NOT NULL CHECK(status IN ('upcoming','live','sold','cancelled')),
  start_time     DATETIME NOT NULL,
  end_time       DATETIME NOT NULL,
  created_at     DATETIME NOT NULL,
  CHECK (end_time > start_time)
);

CREATE TABLE asset_images (
  image_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id   INTEGER NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
  file_path  VARCHAR(255) NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE bids (
  bid_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id   INTEGER NOT NULL REFERENCES assets(asset_id),
  user_id    INTEGER NOT NULL REFERENCES users(user_id),
  bid_amount DECIMAL(12,2) NOT NULL,
  placed_at  DATETIME NOT NULL
);

CREATE TABLE kyc_documents (
  kyc_id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id         INTEGER NOT NULL REFERENCES users(user_id),
  document_type   VARCHAR(30) NOT NULL,
  document_number VARCHAR(50) NOT NULL,
  file_path       VARCHAR(255) NOT NULL,
  status          VARCHAR(10) NOT NULL CHECK(status IN ('pending','approved','rejected')) DEFAULT 'pending',
  reviewed_by     INTEGER REFERENCES users(user_id),
  reviewed_at     DATETIME,
  submitted_at    DATETIME NOT NULL
);

CREATE TABLE deposits (
  deposit_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(user_id),
  asset_id    INTEGER NOT NULL REFERENCES assets(asset_id),
  amount      DECIMAL(12,2) NOT NULL,
  status      VARCHAR(10) NOT NULL CHECK(status IN ('paid','held','refunded','forfeited')),
  created_at  DATETIME NOT NULL
);

CREATE TABLE transactions (
  transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id       INTEGER NOT NULL UNIQUE REFERENCES assets(asset_id),
  buyer_id       INTEGER NOT NULL REFERENCES users(user_id),
  final_amount   DECIMAL(12,2) NOT NULL,
  payment_status VARCHAR(10) NOT NULL,
  created_at     DATETIME NOT NULL,
  paid_at        DATETIME
);
