# Public Asset Auction and Bidding System

A real-time auction platform for Uganda public assets — government vehicles, land, and equipment. Sellers list assets, bidders register, complete KYC, place deposits, and bid in real time. Every bid is recorded atomically with `BEGIN IMMEDIATE` to prevent race conditions. The auction engine is FastAPI + SQLite + SQLModel, and the mobile client is Flutter.

## Group Members

| Name | Registration No. | Role |
|---|---|---|
| Kivumbi Adrian | 241-21301-7621 | Backend Lead |
| Odong Jamil | — | Flutter Lead |
| Nabukeera Mariam | — | Analyst & Integration Lead |

## Project Idea

Government agencies in Uganda auction off surplus assets — old vehicles, unused land, decommissioned equipment — through slow, physical, paper-based processes. Bidders must travel to central locations, sometimes hundreds of kilometres, to attend auctions that end in minutes. Bid amounts are recorded on paper and later transcribed, opening the door to errors and fraud.

This system digitises the entire workflow:

- **Sellers** post assets with descriptions, images, reserve prices, and schedules
- **Bidders** register, complete KYC, place deposits as collateral, and bid in real time
- **Admins** approve KYC documents and monitor auctions
- **Every bid, deposit, and transaction** is recorded immutably in a relational database

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13 · FastAPI · Uvicorn |
| Database | SQLite (file: `backend/auction.db`) |
| ORM | SQLModel (Pydantic + SQLAlchemy) |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| API Docs | OpenAPI 3 auto-generated · Swagger UI at `/docs` |
| Mobile (planned) | Flutter |

## Quick Start — Backend

**Requirements:** Python 3.11+

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
python seed.py              # creates auction.db and seeds demo data
uvicorn main:app --reload --port 3000