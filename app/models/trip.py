# app/models/trip.py
from .base_imports import Base, Column, Integer, ForeignKey, DateTime, Numeric, relationship

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False, index=True)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    route = relationship("Route", back_populates="trips")
    bus = relationship("Bus", back_populates="trips")
    seats = relationship("Seat", back_populates="trip", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="trip")