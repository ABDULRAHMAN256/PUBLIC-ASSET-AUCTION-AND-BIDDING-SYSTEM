# seed.py — insert sample data for testing / demo
from database import get_db, init_db
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta

# Ensure schema exists before we insert (idempotent — safe to call every time)
init_db()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
now = datetime.now(timezone.utc).isoformat()

conn = get_db()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) AS c FROM users")
if cursor.fetchone()["c"] > 0:
    print("[seed] Users exist. Delete auction.db to reseed.")
    raise SystemExit(0)


def add_user(username, email, password, full_name, phone, role, kyc):
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name, phone, role, kyc_status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (username, email, pwd_context.hash(password), full_name, phone, role, kyc, now),
    )
    return cursor.lastrowid


for name in ["Vehicles", "Real Estate", "Equipment"]:
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))


add_user("admin",        "admin@upauction.ug", "admin123",  "System Admin",           "+256700000000", "admin",  "approved")
add_user("seller_mot",   "s1@upauction.ug",    "seller123", "Ministry of Transport",  "+256711111111", "seller", "approved")
add_user("seller_lands", "s2@upauction.ug",    "seller123", "Lands Commission",       "+256722222222", "seller", "approved")
add_user("bidder_john",  "john@upauction.ug",  "bidder123", "John Doe",               "+256733333333", "bidder", "approved")


cursor.execute("SELECT user_id FROM users WHERE username='seller_mot'")
s1 = cursor.fetchone()["user_id"]
cursor.execute("SELECT user_id FROM users WHERE username='seller_lands'")
s2 = cursor.fetchone()["user_id"]
cursor.execute("SELECT category_id FROM categories WHERE name='Vehicles'")
cVeh = cursor.fetchone()["category_id"]
cursor.execute("SELECT category_id FROM categories WHERE name='Real Estate'")
cProp = cursor.fetchone()["category_id"]
cursor.execute("SELECT category_id FROM categories WHERE name='Equipment'")
cEq = cursor.fetchone()["category_id"]


def iso(**kw):
    return (datetime.now(timezone.utc) + timedelta(**kw)).isoformat()


def add_asset(seller, cat, title, desc, sp, rp, inc, status, start, end):
    cursor.execute(
        "INSERT INTO assets (seller_id, category_id, title, description, starting_price, "
        "reserve_price, min_increment, current_price, status, start_time, end_time, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (seller, cat, title, desc, sp, rp, inc, sp, status, start, end, now),
    )
    return cursor.lastrowid


a1 = add_asset(s1, cVeh,  "Toyota Land Cruiser V8", "Ex-Ministry.",     45000000.00, 60000000.00,   500000.00, "live",     iso(days=-1), iso(days=2))
a2 = add_asset(s2, cProp, "Plot 0.5 Acres Kololo",  "Freehold title.", 800000000.00, 900000000.00, 10000000.00, "upcoming", iso(days=3),  iso(days=10))
a3 = add_asset(s1, cEq,   "JCB 3CX Backhoe",        "Ex-UNRA.",        120000000.00, 150000000.00,  1000000.00, "live",     iso(days=-2), iso(hours=6))

for asset_id, url in [
    (a1, "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=800"),
    (a2, "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800"),
    (a3, "https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=800"),
]:
    cursor.execute(
        "INSERT INTO asset_images (asset_id, file_path, is_primary) VALUES (?, ?, 1)",
        (asset_id, url),
    )

conn.commit()
conn.close()
print("Seed complete.")
