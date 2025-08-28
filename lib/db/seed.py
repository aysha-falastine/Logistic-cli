# lib/db/seed.py
from datetime import date, timedelta
import random
from typing import Set

from faker import Faker

from lib.db.database import SessionLocal
from lib.db.models import Truck, FuelLog, Driver

fake = Faker()
random.seed(42)
Faker.seed(42)

COMMON_VENDORS = ["Total", "Shell", "Oryx", "Gulf", "Lake Oil", "Puma", "Engen"]
COMMON_LOCATIONS = ["Depot A", "Depot B", "Main Yard", "Dar es Salaam", "Arusha", "Mwanza", "Dodoma"]


# ---------- helpers ----------
def clear_all(session):
    """Delete rows in FK-safe order so you can reseed anytime."""
    session.query(FuelLog).delete()
    session.query(Driver).delete()
    session.query(Truck).delete()
    session.commit()


def make_plate(existing: Set[str]) -> str:
    """Generate a unique plate like T-123-ABC."""
    while True:
        plate = f"T-{random.randint(100, 999)}-{fake.pystr(min_chars=3, max_chars=3).upper()}"
        if plate not in existing:
            existing.add(plate)
            return plate


# ---------- seeders ----------
def seed_trucks(session, n_trucks=4):
    plates: Set[str] = set()
    statuses = ["active", "maintenance", "retired"]
    trucks = []

    for _ in range(n_trucks):
        plate = make_plate(plates)
        capacity = random.choice([8000, 10000, 12000, 15000, 20000])
        status = random.choice(statuses)
        t = Truck.create(session, plate=plate, capacity_liters=float(capacity), status=status)
        trucks.append(t)

    print(f"Seeded {len(trucks)} trucks.")
    return trucks


def seed_drivers(session, n=5, trucks=None, assign_prob=0.6):
    """Create drivers; some are assigned to random trucks."""
    names = ["Asha Yusuf", "John Mkapa", "Neema Ally", "Peter Kim", "Zainab Juma", "David Mwangi"]
    created = []
    used_licenses: Set[str] = set()

    for _ in range(n):
        name = random.choice(names)
        # unique-ish license numbers
        while True:
            lic = f"LIC-{random.randint(1000, 9999)}"
            if lic not in used_licenses:
                used_licenses.add(lic)
                break
        phone = f"+2557{random.randint(0, 99999999):08d}"
        status = random.choice(["active", "active", "suspended", "inactive"])

        d = Driver.create(session, name=name, license_number=lic, phone=phone, status=status)

        # optionally attach to a truck
        if trucks and random.random() < assign_prob:
            d.assigned_truck = random.choice(trucks)
            session.commit()

        created.append(d)

    print(f"Seeded {len(created)} drivers.")
    return created


def seed_fuel_logs(session, trucks, logs_per_truck_range=(3, 6)):
    """Create several fuel logs per truck with reasonable values."""
    count = 0
    today = date.today()

    for t in trucks:
        n_logs = random.randint(*logs_per_truck_range)
        # start with a base odometer so logs look consistent
        odo = random.uniform(10_000, 600_000)

        for _ in range(n_logs):
            d = today - timedelta(days=random.randint(0, 30))
            liters = round(random.uniform(50.0, 500.0), 1)
            price = round(random.uniform(2.0, 4.5), 2)
            vendor = random.choice(COMMON_VENDORS + [fake.company()])
            location = random.choice(COMMON_LOCATIONS + [fake.city()])
            odo += random.uniform(50.0, 600.0)
            note = random.choice(["", "", "top-up", "full tank", "promo price"]) or None

            FuelLog.create(
                session,
                truck_id=t.id,
                date=d,
                liters=liters,
                price_per_liter=price,
                vendor=vendor,
                location=location,
                odometer=round(odo, 1),
                note=note,
            )
            count += 1

    print(f"Seeded {count} fuel logs.")
    return count


# ---------- entry ----------
def main():
    session = SessionLocal()
    try:
        clear_all(session)
        trucks = seed_trucks(session, n_trucks=4)
        seed_drivers(session, n=6, trucks=trucks, assign_prob=0.7)
        seed_fuel_logs(session, trucks, logs_per_truck_range=(3, 5))
        print("✅ Seeding complete.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
