# routes/transactions.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from database import get_session
from models import Transaction
from auth import get_current_user

router = APIRouter()


@router.get("/me")
def my_transactions(
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    txns = session.exec(
        select(Transaction).where(Transaction.buyer_id == user["id"]).order_by(Transaction.created_at.desc())
    ).all()
    return [t.model_dump() for t in txns]