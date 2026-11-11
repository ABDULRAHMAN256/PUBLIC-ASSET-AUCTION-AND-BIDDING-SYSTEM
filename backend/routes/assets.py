# routes/assets.py â€” Assets CRUD endpoints
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import Optional
from database import get_session
from models import Asset, AssetImage, Category
from auth import get_current_user
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


class AssetCreate(BaseModel):
    category_id: int
    title: str
    description: Optional[str] = None
    starting_price: float
    reserve_price: float
    min_increment: float
    start_time: str
    end_time: str
    images: Optional[list[str]] = None


class AssetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reserve_price: Optional[float] = None
    min_increment: Optional[float] = None
    end_time: Optional[str] = None


@router.get("/")
def list_assets(
    category: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(Asset)
    if category:
        if category.isdigit():
            statement = statement.where(Asset.category_id == int(category))
        else:
            cat = session.exec(select(Category).where(Category.name == category)).first()
            if not cat:
                return []
            statement = statement.where(Asset.category_id == cat.category_id)
    if search:
        statement = statement.where(Asset.title.contains(search) | Asset.description.contains(search))
    if status and status in ("upcoming", "live", "sold", "cancelled"):
        statement = statement.where(Asset.status == status)
    assets = session.exec(statement).all()
    return [a.model_dump() for a in assets]


@router.get("/{asset_id}")
def get_asset(asset_id: int, user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    images = session.exec(select(AssetImage).where(AssetImage.asset_id == asset_id)).all()
    return {"asset": asset.model_dump(), "images": [img.model_dump() for img in images]}


@router.post("/", status_code=201)
def create_asset(
    body: AssetCreate,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user["role"] not in ("seller", "admin"):
        raise HTTPException(status_code=403, detail="Only sellers or admins can create assets")

    if body.reserve_price < body.starting_price:
        raise HTTPException(status_code=400, detail="reserve_price must be >= starting_price")
    if body.min_increment <= 0:
        raise HTTPException(status_code=400, detail="min_increment must be > 0")
    if body.end_time <= body.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    cat = session.get(Category, body.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="category_id not found")

    new_asset = Asset(
        seller_id=user["id"],
        category_id=body.category_id,
        title=body.title,
        description=body.description,
        starting_price=body.starting_price,
        reserve_price=body.reserve_price,
        min_increment=body.min_increment,
        current_price=body.starting_price,
        status="upcoming",
        start_time=datetime.fromisoformat(body.start_time.replace("Z", "+00:00")),
        end_time=datetime.fromisoformat(body.end_time.replace("Z", "+00:00")),
        created_at=datetime.now(timezone.utc),
    )
    session.add(new_asset)
    session.commit()
    session.refresh(new_asset)

    if body.images:
        for i, url in enumerate(body.images[:5]):
            session.add(AssetImage(asset_id=new_asset.asset_id, file_path=url, is_primary=(i == 0)))
        session.commit()

    return {"asset_id": new_asset.asset_id}


@router.put("/{asset_id}")
def update_asset(
    asset_id: int,
    body: AssetUpdate,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user["role"] not in ("seller", "admin"):
        raise HTTPException(status_code=403, detail="Only sellers or admins can update assets")

    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if user["role"] != "admin" and asset.seller_id != user["id"]:
        raise HTTPException(status_code=403, detail="You can only update your own assets")

    if asset.status == "sold":
        raise HTTPException(status_code=400, detail="Sold assets are immutable")

    changed = False
    for field in ("title", "description", "reserve_price", "min_increment"):
        value = getattr(body, field)
        if value is not None:
            setattr(asset, field, value)
            changed = True
    if body.end_time is not None:
        asset.end_time = datetime.fromisoformat(body.end_time.replace("Z", "+00:00"))
        changed = True
    if not changed:
        raise HTTPException(status_code=400, detail="No fields to update")

    session.add(asset)
    session.commit()
    return {"updated": True}


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user["role"] not in ("seller", "admin"):
        raise HTTPException(status_code=403, detail="Only sellers or admins can delete assets")

    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if user["role"] != "admin" and asset.seller_id != user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own assets")

    if asset.status == "live":
        raise HTTPException(status_code=409, detail="Cannot delete a live asset")

    session.delete(asset)
    session.commit()
    return {"deleted": True}
