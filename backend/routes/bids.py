# routes/bids.py - atomic bidding engine
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from database import get_session, engine
from models import Bid, Asset
from auth import get_current_user
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy import text

router = APIRouter()

class BidCreate(BaseModel):
    asset_id: int
    bid_amount: float

@router.post("/", status_code=201)
def place_bid(body: BidCreate, user: dict = Depends(get_current_user)):
    if body.bid_amount <= 0:
        raise HTTPException(status_code=400, detail="bid_amount must be positive")
    with engine.connect() as conn:
        try:
            conn.execute(text("BEGIN IMMEDIATE"))
        except Exception:
            raise HTTPException(status_code=409, detail="Auction is busy, retry")
        try:
            row = conn.execute(
                text("SELECT current_price, status, end_time, min_increment FROM assets WHERE asset_id = :aid"),
                {"aid": body.asset_id}
            ).fetchone()
            if row is None:
                conn.execute(text("ROLLBACK"))
                raise HTTPException(status_code=404, detail="Asset not found")
            current_price = row[0]
            status = row[1]
            end_time_str = row[2]
            min_increment = row[3]
            if status != "live":
                conn.execute(text("ROLLBACK"))
                raise HTTPException(status_code=409, detail=f"Asset is {status}, cannot bid")
            now = datetime.now(timezone.utc)
            try:
                end_time = datetime.fromisoformat(end_time_str)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                conn.execute(text("ROLLBACK"))
                raise HTTPException(status_code=500, detail="Invalid end_time")
            if now > end_time:
                conn.execute(text("ROLLBACK"))
                raise HTTPException(status_code=409, detail="Auction has ended")
            minimum_bid = current_price + min_increment
            if body.bid_amount < minimum_bid:
                conn.execute(text("ROLLBACK"))
                raise HTTPException(status_code=400, detail=f"Bid too low. Minimum is {minimum_bid}")
            conn.execute(
                text("INSERT INTO bids (asset_id, user_id, bid_amount, placed_at) VALUES (:aid, :uid, :amt, :now)"),
                {"aid": body.asset_id, "uid": user["id"], "amt": body.bid_amount, "now": now.isoformat()}
            )
            conn.execute(
                text("UPDATE assets SET current_price = :amt WHERE asset_id = :aid"),
                {"amt": body.bid_amount, "aid": body.asset_id}
            )
            conn.execute(text("COMMIT"))
        except HTTPException:
            raise
        except Exception as e:
            try:
                conn.execute(text("ROLLBACK"))
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Bid placed", "new_price": body.bid_amount}

@router.get("/assets/{asset_id}/bids")
def list_bids(asset_id: int, user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    bids = session.exec(select(Bid).where(Bid.asset_id == asset_id).order_by(Bid.bid_amount.desc())).all()
    return [b.model_dump() for b in bids]

@router.get("/users/me/bids")
def my_bids(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    bids = session.exec(select(Bid).where(Bid.user_id == user["id"]).order_by(Bid.bid_amount.desc())).all()
    return [b.model_dump() for b in bids]
