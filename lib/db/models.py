# lib/db/models.py
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, validates

Base = declarative_base()

# Mixin for CRUD operations to avoid repetition
from sqlalchemy.orm import Session

class CRUDMixin:
    @classmethod
    def create(cls, session: Session, **kwargs):
        obj = cls(**kwargs)  # kwargs is keyword arguments for the model
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    @classmethod
    def get_all(cls, session: Session):
        return session.query(cls).all()

    @classmethod
    def find_by_id(cls, session: Session, id_):
        return session.get(cls, id_)

    @classmethod
    def delete(cls, session: Session, id_):
        obj = session.get(cls, id_)
        if not obj:
            return False
        session.delete(obj)
        session.commit()
        return True


class Truck(Base, CRUDMixin):
    __tablename__ = "trucks"
# defining truck table
    id = Column(Integer, primary_key=True)
    plate = Column(String, unique=True, nullable=False)
    capacity_liters = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="active")

    fuel_logs = relationship("FuelLog", back_populates="truck", cascade="all, delete-orphan") # one-to-many with FuelLog
    drivers = relationship("Driver", back_populates="assigned_truck") # one-to-many with Driver (reverse relationship to trucks)

# Validations for Truck fields
    @validates("plate")
    def _plate(self, k, v):
        v = (v or "").strip().upper()
        if len(v) < 3:
            raise ValueError("Plate must be at least 3 characters.")
        return v

    @validates("capacity_liters")
    def _cap(self, k, v):
        v = float(v)
        if v <= 0:
            raise ValueError("Capacity (liters) must be > 0.")
        return v

    @validates("status")
    def _status(self, k, v):
        allowed = {"active", "maintenance", "retired"}
        v = (v or "").strip().lower()
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}.")
        return v


class FuelLog(Base, CRUDMixin):
    __tablename__ = "fuel_logs"
# defining fuel log table
    id = Column(Integer, primary_key=True)
    truck_id = Column(Integer, ForeignKey("trucks.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    liters = Column(Float, nullable=False)
    price_per_liter = Column(Float, nullable=False)
    vendor = Column(String, nullable=False)
    location = Column(String, nullable=False)
    odometer = Column(Float, nullable=False, default=0.0)
    note = Column(String, nullable=True)

    truck = relationship("Truck", back_populates="fuel_logs")

# Validations for FuelLog fields
    @validates("liters", "price_per_liter")
    def _positive(self, k, v):
        v = float(v)
        if v <= 0:
            raise ValueError(f"{k} must be > 0")
        return v

    @validates("vendor", "location")
    def _nonempty(self, k, v):
        v = (v or "").strip()
        if not v:
            raise ValueError(f"{k} cannot be empty")
        return v

    @validates("odometer")
    def _odo(self, k, v):
        v = float(v)
        if v < 0:
            raise ValueError("odometer must be >= 0")
        return v



# Driver model with optional truck assignment

class Driver(Base, CRUDMixin):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    license_number = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")

    # I added optional assignment to a truck where many drivers → one truck.
    assigned_truck_id = Column(Integer, ForeignKey("trucks.id"), nullable=True)
    assigned_truck = relationship("Truck", back_populates="drivers")

# Validations for Driver fields
    @validates("name")
    def _name(self, k, v):
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return v

    @validates("license_number")
    def _lic(self, k, v):
        v = (v or "").strip().upper()
        if len(v) < 4:
            raise ValueError("License number must be at least 4 characters.")
        return v

    @validates("status")
    def _status(self, k, v):
        allowed = {"active", "suspended", "inactive"}
        v = (v or "").strip().lower()
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}.")
        return v
