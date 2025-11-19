# app/models/route.py
from .base_imports import Base, Column, Integer, String, relationship

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True)
    origin = Column(String(100), nullable=False, index=True)
    destination = Column(String(100), nullable=False, index=True)
    distance_km = Column(Integer)

    trips = relationship("Trip", back_populates="route")