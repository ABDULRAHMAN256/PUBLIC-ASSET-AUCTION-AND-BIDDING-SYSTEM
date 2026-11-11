# routes/kyc.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from database import get_session
from models import KYCDocument, User
from auth import get_current_user
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


class KYCCreate(BaseModel):
    document_type: str
    document_number: str
    file_path: str


@router.post("/", status_code=201)
def submit_kyc(
    body: KYCCreate,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user["role"] not in ("bidder", "seller"):
        raise HTTPException(status_code=403, detail="Only bidders and sellers submit KYC")

    doc = KYCDocument(
        user_id=user["id"],
        document_type=body.document_type,
        document_number=body.document_number,
        file_path=body.file_path,
        status="pending",
        submitted_at=datetime.now(timezone.utc),
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return {"kyc_id": doc.kyc_id}


@router.post("/{kyc_id}/approve")
def approve_kyc(
    kyc_id: int,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can approve KYC")

    doc = session.get(KYCDocument, kyc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="KYC not found")

    doc.status = "approved"
    doc.reviewed_by = user["id"]
    doc.reviewed_at = datetime.now(timezone.utc)
    session.add(doc)

    target_user = session.get(User, doc.user_id)
    if target_user:
        target_user.kyc_status = "approved"
        session.add(target_user)

    session.commit()
    return {"approved": True}