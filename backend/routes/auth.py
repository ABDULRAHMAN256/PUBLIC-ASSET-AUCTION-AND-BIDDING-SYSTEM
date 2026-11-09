# routes/auth.py — Register and Login endpoints
from fastapi import APIRouter, HTTPException
from database import get_db
from models import RegisterRequest, LoginRequest
from auth import hash_password, verify_password, create_access_token
from datetime import datetime, timezone

router = APIRouter()

@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM users WHERE username = ? OR email = ?", (body.username, body.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")

    now = datetime.now(timezone.utc).isoformat()
    hashed = hash_password(body.password)

    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name, phone, role, kyc_status, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'bidder', 'pending', ?)",
        (body.username, body.email, hashed, body.full_name, body.phone, now)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    token = create_access_token(user_id, "bidder")
    return {"token": token, "user_id": user_id}

@router.post("/login")
def login(body: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password_hash, role FROM users WHERE username = ? OR email = ?", (body.username, body.username))
    row = cursor.fetchone()
    conn.close()

    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(row["user_id"], row["role"])
    return {"token": token}
