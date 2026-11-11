# seed.py — Insert sample data using SQLModel Session
from sqlmodel import Session, select
from database import engine, init_db
from models import User, Category, Asset, AssetImage
from auth import hash_password
from datetime import datetime, timedelta, timezone


def seed():
    init_db()
    with Session(engine) as session:
        if session.exec(select(User)).first():
            print("[seed] Users exist. Delete auction.db to reseed.")
            return

        for name in ["Vehicles", "Real Estate", "Equipment"]:
            session.add(Category(name=name))
        session.commit()

        users = [
            User(username="admin", email="admin@upauction.ug", password_hash=hash_password("admin123"),
                 full_name="System Admin", phone="+256700000000", role="admin", kyc_status="approved",
                 created_at=datetime.now(timezone.utc)),
            User(username="seller_mot", email="s1@upauction.ug", password_hash=hash_password("seller123"),
                 full_name="Ministry of Transport", phone="+256711111111", role="seller", kyc_status="approved",
                 created_at=datetime.now(timezone.utc)),
            User(username="seller_lands", email="s2@upauction.ug", password_hash=hash_password("seller123"),
                 full_name="Lands Commission", phone="+256722222222", role="seller", kyc_status="approved",
                 created_at=datetime.now(timezone.utc)),
            User(username="bidder_john", email="john@upauction.ug", password_hash=hash_password("bidder123"),
                 full_name="John Doe", phone="+256733333333", role="bidder", kyc_status="approved",
                 created_at=datetime.now(timezone.utc)),
        ]
        for u in users:
            session.add(u)
        session.commit()

        sm = session.exec(select(User).where(User.username == "seller_mot")).first()
        sl = session.exec(select(User).where(User.username == "seller_lands")).first()
        veh = session.exec(select(Category).where(Category.name == "Vehicles")).first()
        prop = session.exec(select(Category).where(Category.name == "Real Estate")).first()
        eq = session.exec(select(Category).where(Category.name == "Equipment")).first()
        now = datetime.now(timezone.utc)

        assets = [
            Asset(seller_id=sm.user_id, category_id=veh.category_id, title="Toyota Land Cruiser V8",
                  description="Ex-Ministry.", starting_price=45000000, reserve_price=60000000,
                  min_increment=500000, current_price=45000000, status="live",
                  start_time=now - timedelta(days=1), end_time=now + timedelta(days=2), created_at=now),
            Asset(seller_id=sl.user_id, category_id=prop.category_id, title="Plot 0.5 Acres Kololo",
                  description="Freehold title.", starting_price=800000000, reserve_price=900000000,
                  min_increment=10000000, current_price=800000000, status="upcoming",
                  start_time=now + timedelta(days=3), end_time=now + timedelta(days=10), created_at=now),
            Asset(seller_id=sm.user_id, category_id=eq.category_id, title="JCB 3CX Backhoe",
                  description="Ex-UNRA.", starting_price=120000000, reserve_price=150000000,
                  min_increment=1000000, current_price=120000000, status="live",
                  start_time=now - timedelta(days=2), end_time=now + timedelta(hours=6), created_at=now),
        ]
        for a in assets:
            session.add(a)
        session.commit()

        for aid, url in [
            (assets[0].asset_id, "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=800"),
            (assets[1].asset_id, "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800"),
            (assets[2].asset_id, "https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=800"),
        ]:
            session.add(AssetImage(asset_id=aid, file_path=url, is_primary=True))
        session.commit()

        print("Seed complete.")


if __name__ == "__main__":
    seed()