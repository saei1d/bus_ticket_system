# app/models/booking.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String, func, Index, Date
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    price_paid = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="confirmed")  # confirmed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    booking_date = Column(Date, server_default=func.current_date(), nullable=False, index=True)

    user = relationship("User", back_populates="bookings")
    trip = relationship("Trip", back_populates="bookings")
    seat = relationship("Seat", back_populates="booking")

    __table_args__ = (
        Index('ix_user_booking_date', user_id, booking_date),
    )