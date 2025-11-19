# app/models/seat.py
from .base_imports import Base, Column, Integer, ForeignKey, Boolean, UniqueConstraint, relationship

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    seat_number = Column(Integer, nullable=False)
    is_reserved = Column(Boolean, default=False, index=True)

    trip = relationship("Trip", back_populates="seats")
    booking = relationship("Booking", back_populates="seat", uselist=False)

    __table_args__ = (UniqueConstraint('trip_id', 'seat_number', name='uix_trip_seat'),)