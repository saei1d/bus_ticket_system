# app/models/bus.py
from .base_imports import Base, Column, Integer, String, Boolean, relationship

class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True)
    plate_number = Column(String(20), unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    is_vip = Column(Boolean, default=False)

    trips = relationship("Trip", back_populates="bus")