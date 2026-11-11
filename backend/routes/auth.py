# routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from database import get_session
from models import User, RegisterRequest, LoginRequest
from auth import hash_password, verify_password, create_access_token
from datetime import datetime, timezone

router = APIRouter()


@router.post("/register", status_code=201)
def register(body: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(
        select(User).where((User.username == body.username) | (User.email == body.email))
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
        role="bidder",
        kyc_status="pending",
        created_at=datetime.now(timezone.utc),
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    token = create_access_token(new_user.user_id, "bidder")
    return {"token": token, "user_id": new_user.user_id}


@router.post("/login")
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where((User.username == body.username) | (User.email == body.username))
    ).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.user_id, user.role)
    return {"token": token}