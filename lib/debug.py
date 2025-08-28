# lib/debug.py
from lib.db.database import SessionLocal
from lib.db.models import Truck

db = SessionLocal()

# Quick test: list trucks
for truck in db.query(Truck).all():
    print(truck.id, truck.plate_number)
