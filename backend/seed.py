"""
seed.py — Initialises the S.O.S. database with:
  • 1 Admin account
  • 3 Authority accounts (Electrical, Civil/Maintenance, Security)
  • 66 real SRM KTR campus buildings (with plinth areas + criticality)

No fake reports or demo student data are seeded.
Run: python seed.py
"""
import sys
import os

# Make sure app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models import User, Location, UserRole
from app.core.config import get_settings
from passlib.context import CryptContext

settings = get_settings()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pw(pw: str) -> str:
    return pwd_ctx.hash(pw)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ── Admin + Authority accounts ────────────────────────────────────────────
    accounts = [
        {
            "name": "Admin",
            "email": "admin@university.edu",
            "password": "admin123",
            "role": UserRole.admin,
            "department": None,
        },
        {
            "name": "Electrical Authority",
            "email": "electrical@university.edu",
            "password": "auth123",
            "role": UserRole.authority,
            "department": "Electrical",
        },
        {
            "name": "Civil Authority",
            "email": "civil@university.edu",
            "password": "auth123",
            "role": UserRole.authority,
            "department": "Civil/Maintenance",
        },
        {
            "name": "Security Authority",
            "email": "security@university.edu",
            "password": "auth123",
            "role": UserRole.authority,
            "department": "Security",
        },
        {
            "name": "Demo Student",
            "email": "student@university.edu",
            "password": "student123",
            "role": UserRole.student,
            "department": None,
        },
    ]

    for acc in accounts:
        if not db.query(User).filter(User.email == acc["email"]).first():
            db.add(User(
                name=acc["name"],
                email=acc["email"],
                password_hash=hash_pw(acc["password"]),
                role=acc["role"],
                department=acc["department"],
            ))
            print(f"  + User: {acc['email']}")
        else:
            print(f"  ~ Exists: {acc['email']}")

    db.commit()

    # ── Campus Buildings ──────────────────────────────────────────────────────
    # (building, zone, criticality 1-5, plinth_area sq.m)
    # Criticality: 5=labs/high-risk, 4=hostels/academic, 3=admin/library, 2=services, 1=parking/ancillary
    buildings = [
        # Academic / Technical Blocks
        ("Main Block", "Ground Floor",       4, 5630.00),
        ("Main Block", "Upper Floors",       4, 5630.00),
        ("University Building", "Wing A",    3, 4200.00),
        ("University Building", "Wing B",    3, 4200.00),
        ("Computer Science Block", None,     4, 2800.00),
        ("PG Block", None,                   4, 1950.00),
        ("S&H Block", None,                  3, 1800.00),
        ("MBA Block", None,                  4, 3200.00),
        ("New MBA Block (Law)", None,        3, 2500.00),
        ("B.Arch Block", None,               4, 1600.00),
        ("Kalam Block", None,                4, 3100.00),
        ("CRC Block", None,                  3, 2200.00),
        # Engineering Labs & Workshops
        ("Electrical Science Block", None,   5, 2150.00),
        ("Bio Tech Block", None,             5, 1980.00),
        ("Hi Tech Block", None,              5, 2400.00),
        ("Basic Engineering Lab", None,      5, 1750.00),
        ("Chemical Block", None,             5, 1850.00),
        ("Chemistry Research", None,         5, 1200.00),
        ("Raman Research Park", None,        4, 2000.00),
        ("iOS Development Centre", None,     4, 1100.00),
        # Mechanical & Aerospace
        ("Mechanical Block A", None,         5, 2100.00),
        ("Mechanical Block B", None,         5, 2100.00),
        ("Mechanical Block C", None,         5, 2100.00),
        ("Mechanical Block D", None,         5, 2100.00),
        ("Mechanical Block E", None,         5, 2100.00),
        ("Mechanical Hanger", None,          5, 3500.00),
        ("Aerospace Hanger", None,           5, 4200.00),
        ("Automobile Block", None,           5, 1900.00),
        # IT / Tech Parks
        ("IT Park", "Block A",               4, 3800.00),
        ("IT Park", "Block B",               4, 3800.00),
        ("Tech Park 1", "Ground Floor",      4, 4500.00),
        ("Tech Park 1", "Upper Floors",      4, 4500.00),
        ("Tech Park 2", None,                4, 4500.00),
        # Library & Admin
        ("Library Building", None,           3, 3600.00),
        ("Administrative Building", None,    3, 2900.00),
        ("Estate Office", None,              2, 600.00),
        ("Post Office", None,                1, 200.00),
        # Auditorium & Events
        ("Auditorium", None,                 3, 2800.00),
        # Hostels
        ("Sannasi Hostel IV", "Block A",     4, 5200.00),
        ("Sannasi Hostel IV", "Block B",     4, 5200.00),
        ("New Ladies Hostel A", None,        4, 3800.00),
        ("International Hostel", "Male",     4, 2600.00),
        ("International Hostel", "Female",   4, 2600.00),
        # Canteen & Food
        ("Canteen Building", None,           2, 1200.00),
        ("Canteen Extension", None,          2, 600.00),
        ("Java Green", None,                 2, 400.00),
        # Sports & Recreation
        ("Gymnasium", None,                  3, 1100.00),
        ("Swimming Pool", None,              3, 800.00),
        # Health & Services
        ("Medical Centre", None,             4, 500.00),
        ("Guest House", None,                2, 800.00),
        # Security
        ("Main Gate Security Post", None,    3, 150.00),
        ("Police Outpost", None,             3, 120.00),
        # Parking & Utilities
        ("Vehicle Parking (North)", None,    1, 2000.00),
        ("Vehicle Parking (South)", None,    1, 1800.00),
        ("Power House", None,                5, 700.00),
        ("Pump House", None,                 4, 300.00),
        ("Waste Management Unit", None,      3, 400.00),
        ("Solar Panel Area", None,           2, 1500.00),
        ("Transformer Yard", None,           5, 350.00),
        # Outdoor / Campus Areas
        ("Main Entrance Plaza", None,        2, None),
        ("Central Lawn",         None,       2, None),
        ("Sports Ground",        None,       2, None),
        ("Sculpture Garden",     None,       1, None),
        ("Campus Road Network",  None,       2, None),
        ("Rainwater Harvesting Pond", None,  2, None),
    ]

    # Remove all existing locations so we get a clean set
    db.query(Location).delete()
    db.commit()

    for building, zone, criticality, plinth_area in buildings:
        db.add(Location(
            building=building,
            zone=zone,
            criticality=criticality,
            plinth_area=plinth_area,
        ))

    db.commit()
    print(f"\n✅ Seeded {len(buildings)} campus locations.")
    print("\n── Login Credentials ───────────────────────────────")
    print("  Admin      : admin@university.edu        / admin123")
    print("  Electrical : electrical@university.edu   / auth123")
    print("  Civil      : civil@university.edu        / auth123")
    print("  Security   : security@university.edu     / auth123")
    print("────────────────────────────────────────────────────")
    print("No demo reports seeded. Reports are created by users via the app.")


if __name__ == "__main__":
    seed()
