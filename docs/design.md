# Public Asset Auction and Bidding System
## Design Document

**Course:** Mobile App Development Capstone  
**Group:** KIVUMBI ADRIAN (Backend Lead), ODONG JAMIL (Flutter Lead), NABUKEERA MARIAM (Analyst)  
**Submission date:** 20 November 2026

---

## 1. Problem Statement

Public assets in Uganda — government vehicles, land, equipment — are currently auctioned through a process that is slow, opaque, and expensive. Sellers must physically transport buyers to a central location, print catalogues, and take bids in person. Bidders often travel hundreds of kilometres to attend auctions that may end in minutes. Corruption is possible because bid amounts are recorded on paper and later transcribed into spreadsheets, with no audit trail.

The **Public Asset Auction and Bidding System** digitises the entire workflow. Sellers post assets with full descriptions, images, and a schedule. Bidders register, complete KYC verification, place deposits as collateral, and bid in real time. Every bid, deposit, and transaction is recorded immutably in a relational database, with full audit trails. A public asset dashboard shows live auctions across all categories, and a mobile app (Flutter) lets bidders participate from anywhere.

**Who benefits:** Government agencies selling surplus assets get wider reach and immutable records; bidders save travel and time and see real-time prices; auditors can query any historical transaction.

---

## 2. Users and Their Goals

| User type | Goal |
|---|---|
| **Bidder** | Register, complete KYC, deposit collateral, browse live auctions, place bids, track bids, receive receipts on won auctions |
| **Seller** | List assets with images and reserve prices, monitor live bids, manage listings |
| **Admin** | Approve/reject KYC documents, pause live auctions, monitor the system |
| **Guest** | Browse catalogue without bidding (public view) |

---

## 3. Functional Requirements

**FR-01.** The system shall allow users to register with username, email, and password.  
**FR-02.** The system shall hash passwords using bcrypt before storage.  
**FR-03.** The system shall issue a JWT upon successful login and register.  
**FR-04.** The system shall verify JWT on every protected endpoint and return 401 on missing/invalid token.  
**FR-05.** The system shall allow sellers and admins to create assets with title, description, category, starting price, reserve price, minimum increment, start time, and end time.  
**FR-06.** The system shall list assets with filtering by category, status, and search by title/description.  
**FR-07.** The system shall allow sellers to update and delete their own assets (but not other sellers').  
**FR-08.** The system shall allow bidders to place a bid on any live asset, provided the bid is at least (current_price + min_increment).  
**FR-09.** The system shall reject bids on non-live assets (upcoming, sold, cancelled) with 409 Conflict.  
**FR-10.** The system shall record every bid atomically with `BEGIN IMMEDIATE` to prevent race conditions.  
**FR-11.** The system shall allow bidders to submit KYC documents (national ID, passport, etc.) for admin approval.  
**FR-12.** The system shall allow admins to approve or reject KYC documents.  
**FR-13.** The system shall allow bidders to record deposits against specific assets as collateral.  
**FR-14.** The system shall return only the requesting user's bids, deposits, and transactions via `/me` endpoints.  
**FR-15.** The system shall expose all endpoints through an OpenAPI 3 spec at `/openapi.json` with Swagger UI at `/docs`.

---

## 4. Non-Functional Requirements

**NFR-01.** The system shall respond to 95% of read requests within 500ms under normal load.  
**NFR-02.** The system shall maintain consistency: no two bids may share the same asset record state simultaneously (guaranteed by SQLite `BEGIN IMMEDIATE`).  
**NFR-03.** The system shall remain usable when the API server is briefly unavailable (Flutter app shows cached data and retries every 3 seconds).  
**NFR-04.** The system shall record timestamps in UTC (ISO-8601) to avoid timezone ambiguity.  
**NFR-05.** The system shall prevent SQL injection via parameterised queries (SQLModel/SQLAlchemy).

---

## 5. User Stories

**US-01.** As a bidder, I want to register with a username and password so I can access the auction platform.  
**US-02.** As a bidder, I want to log in and receive a JWT so my future requests are authenticated.  
**US-03.** As a bidder, I want to browse assets by category so I can find what I'm interested in.  
**US-04.** As a bidder, I want to place a bid above the current price + minimum increment so I can win the item.  
**US-05.** As a bidder, I want to see all my past bids so I can track my activity.  
**US-06.** As a seller, I want to create a listing with images and a reserve price so bidders can evaluate my asset.  
**US-07.** As a seller, I want to edit or delete my listings before they go live so I can correct mistakes.  
**US-08.** As an admin, I want to approve or reject KYC documents so only verified users can bid.

---

## 6. Entity-Relationship Diagram

The complete ERD is included at `docs/erd.png`. Summary:

| Entity | Primary key | Key relationships |
|---|---|---|
| `users` | user_id | 1:N to assets (seller_id), bids (user_id), deposits (user_id), kyc_documents (user_id) |
| `categories` | category_id | 1:N to assets (category_id) |
| `assets` | asset_id | N:1 to users, N:1 to categories; 1:N to asset_images, bids, deposits; 1:1 to transactions |
| `asset_images` | image_id | N:1 to assets |
| `bids` | bid_id | N:1 to assets, N:1 to users |
| `kyc_documents` | kyc_id | N:1 to users (user_id and reviewed_by) |
| `deposits` | deposit_id | N:1 to users, N:1 to assets |
| `transactions` | transaction_id | 1:1 to assets; N:1 to users (buyer_id) |

**Normalisation:** All tables are in 3rd Normal Form. Every non-key column depends only on the primary key. Many-to-many relationships are resolved with junction tables (`bids`, `deposits` link users and assets many-to-many).

---

## 7. Data Dictionary

### 7.1 users

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| user_id | INTEGER | — | PK, auto-increment | Unique user identifier |
| username | VARCHAR | 50 | UNIQUE, NOT NULL | Login handle |
| email | VARCHAR | 255 | UNIQUE, NOT NULL | Email address |
| password_hash | VARCHAR | 255 | NOT NULL | bcrypt-hashed password |
| full_name | VARCHAR | 100 | NULL | Display name |
| phone | VARCHAR | 20 | NULL | Contact phone |
| role | VARCHAR | 10 | CHECK IN ('bidder','seller','admin') | User role |
| kyc_status | VARCHAR | 10 | DEFAULT 'pending' | KYC verification status |
| created_at | DATETIME | — | NOT NULL | Registration timestamp (UTC) |

### 7.2 categories

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| category_id | INTEGER | — | PK, auto-increment | Category identifier |
| name | VARCHAR | 50 | UNIQUE, NOT NULL | Category name |

### 7.3 assets

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| asset_id | INTEGER | — | PK, auto-increment | Asset identifier |
| seller_id | INTEGER | — | FK → users.user_id, NOT NULL | Owner |
| category_id | INTEGER | — | FK → categories.category_id, NOT NULL | Category |
| title | VARCHAR | 150 | NOT NULL | Short title |
| description | TEXT | — | NULL | Full description |
| starting_price | DECIMAL | 12,2 | NOT NULL | Starting bid (UGX) |
| reserve_price | DECIMAL | 12,2 | NOT NULL | Minimum sale price |
| min_increment | DECIMAL | 12,2 | NOT NULL, DEFAULT 500000 | Minimum raise per bid |
| current_price | DECIMAL | 12,2 | NOT NULL | Current highest bid |
| status | VARCHAR | 10 | CHECK IN ('upcoming','live','sold','cancelled') | Auction state |
| start_time | DATETIME | — | NOT NULL | Auction opens |
| end_time | DATETIME | — | NOT NULL, CHECK > start_time | Auction closes |
| created_at | DATETIME | — | NOT NULL | Creation timestamp |

---

### 7.4 asset_images

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| image_id | INTEGER | — | PK, auto-increment | Image identifier |
| asset_id | INTEGER | — | FK → assets.asset_id, NOT NULL | Asset |
| file_path | VARCHAR | 255 | NOT NULL | Image URL or path |
| is_primary | BOOLEAN | — | DEFAULT 0 | Cover image flag |

### 7.5 bids

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| bid_id | INTEGER | — | PK, auto-increment | Bid identifier |
| asset_id | INTEGER | — | FK → assets.asset_id, NOT NULL | Target asset |
| user_id | INTEGER | — | FK → users.user_id, NOT NULL | Bidder |
| bid_amount | DECIMAL | 12,2 | NOT NULL | Bid value (UGX) |
| placed_at | DATETIME | — | NOT NULL | Timestamp (UTC) |

### 7.6 kyc_documents

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| kyc_id | INTEGER | — | PK, auto-increment | Document identifier |
| user_id | INTEGER | — | FK → users.user_id, NOT NULL | Submitting user |
| document_type | VARCHAR | 30 | NOT NULL | e.g. national_id, passport |
| document_number | VARCHAR | 50 | NOT NULL | Document number |
| file_path | VARCHAR | 255 | NOT NULL | Scan URL |
| status | VARCHAR | 10 | CHECK IN ('pending','approved','rejected'), DEFAULT 'pending' | Review status |
| reviewed_by | INTEGER | — | FK → users.user_id, NULL | Admin reviewer |
| reviewed_at | DATETIME | — | NULL | Review timestamp |
| submitted_at | DATETIME | — | NOT NULL | Submission timestamp |

### 7.7 deposits

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| deposit_id | INTEGER | — | PK, auto-increment | Deposit identifier |
| user_id | INTEGER | — | FK → users.user_id, NOT NULL | Depositor |
| asset_id | INTEGER | — | FK → assets.asset_id, NOT NULL | Target asset |
| amount | DECIMAL | 12,2 | NOT NULL | Deposit amount (UGX) |
| status | VARCHAR | 10 | CHECK IN ('paid','held','refunded','forfeited') | Deposit state |
| created_at | DATETIME | — | NOT NULL | Timestamp |

### 7.8 transactions

| Field | Type | Size | Constraints | Meaning |
|---|---|---|---|---|
| transaction_id | INTEGER | — | PK, auto-increment | Transaction identifier |
| asset_id | INTEGER | — | FK → assets.asset_id, UNIQUE, NOT NULL | Sold asset |
| buyer_id | INTEGER | — | FK → users.user_id, NOT NULL | Winning bidder |
| final_amount | DECIMAL | 12,2 | NOT NULL | Sale price |
| payment_status | VARCHAR | 10 | NOT NULL | pending, paid |
| created_at | DATETIME | — | NOT NULL | Transaction created |
| paid_at | DATETIME | — | NULL | Payment confirmed |

---

## 8. API Endpoint Table

Full machine-readable spec: `/openapi.json`. Human-readable: `/docs`.

| # | Method | Path | Purpose | Auth | Request | Response |
|---|---|---|---|---|---|---|
| 1 | POST | /api/auth/register | Register new bidder | No | username, email, password | 201 {token, user_id} |
| 2 | POST | /api/auth/login | Login | No | username, password | 200 {token} |
| 3 | GET | /api/assets/ | List assets | JWT | query: category, search, status | 200 [asset] |
| 4 | GET | /api/assets/{id} | Get one asset | JWT | — | 200 {asset, images} |
| 5 | POST | /api/assets/ | Create asset | JWT (seller/admin) | asset fields | 201 {asset_id} |
| 6 | PUT | /api/assets/{id} | Update asset | JWT (owner/admin) | partial fields | 200 {updated} |
| 7 | DELETE | /api/assets/{id} | Delete asset | JWT (owner/admin) | — | 200 {deleted} |
| 8 | POST | /api/ | Place bid | JWT (any) | asset_id, bid_amount | 201 {new_price} |
| 9 | GET | /api/assets/{id}/bids | Bid history | JWT | — | 200 [bid] |
| 10 | GET | /api/users/me/bids | My bids | JWT | — | 200 [bid] |
| 11 | POST | /api/kyc/ | Submit KYC | JWT (bidder/seller) | document fields | 201 {kyc_id} |
| 12 | POST | /api/kyc/{id}/approve | Approve KYC | JWT (admin) | — | 200 {approved} |
| 13 | POST | /api/deposits/ | Create deposit | JWT | asset_id, amount, payment_ref | 201 {deposit_id} |
| 14 | GET | /api/deposits/me | My deposits | JWT | — | 200 [deposit] |
| 15 | GET | /api/transactions/me | My receipts | JWT | — | 200 [transaction] |
| 16 | GET | /api/health | Health check | No | — | 200 {ok} |

---

## 9. Screen Sketches

Refer to `docs/screens/` (maintained by the Flutter lead): Login, Register, Asset Catalog, Asset Detail (Bidding Room), My Bids, KYC Upload, Deposit, Admin Dashboard.

---

**End of design document.**

## 8. API Endpoint Table

Full machine-readable spec: `/openapi.json`. Human-readable: `/docs`.

| # | Method | Path | Purpose | Auth | Request | Response |
|---|---|---|---|---|---|---|
| 1 | POST | /api/auth/register | Register new bidder | No | username, email, password | 201 {token, user_id} |
| 2 | POST | /api/auth/login | Login | No | username, password | 200 {token} |
| 3 | GET | /api/assets/ | List assets | JWT | query: category, search, status | 200 [asset] |
| 4 | GET | /api/assets/{id} | Get one asset | JWT | ? | 200 {asset, images} |
| 5 | POST | /api/assets/ | Create asset | JWT (seller/admin) | asset fields | 201 {asset_id} |
| 6 | PUT | /api/assets/{id} | Update asset | JWT (owner/admin) | partial fields | 200 {updated} |
| 7 | DELETE | /api/assets/{id} | Delete asset | JWT (owner/admin) | ? | 200 {deleted} |
| 8 | POST | /api/ | Place bid | JWT (any) | asset_id, bid_amount | 201 {new_price} |
| 9 | GET | /api/assets/{id}/bids | Bid history | JWT | ? | 200 [bid] |
| 10 | GET | /api/users/me/bids | My bids | JWT | ? | 200 [bid] |
| 11 | POST | /api/kyc/ | Submit KYC | JWT (bidder/seller) | document fields | 201 {kyc_id} |
| 12 | POST | /api/kyc/{id}/approve | Approve KYC | JWT (admin) | ? | 200 {approved} |
| 13 | POST | /api/deposits/ | Create deposit | JWT | asset_id, amount, payment_ref | 201 {deposit_id} |
| 14 | GET | /api/deposits/me | My deposits | JWT | ? | 200 [deposit] |
| 15 | GET | /api/transactions/me | My receipts | JWT | ? | 200 [transaction] |
| 16 | GET | /api/health | Health check | No | ? | 200 {ok} |

---

## 9. Screen Sketches

Refer to `docs/screens/` (maintained by the Flutter lead): Login, Register, Asset Catalog, Asset Detail (Bidding Room), My Bids, KYC Upload, Deposit, Admin Dashboard.

---

**End of design document.**
