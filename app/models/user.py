# app/models/user.py
from .base_imports import Base, Column, Integer, String, DateTime, func, relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String(11), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    profiles = relationship("Profile", back_populates="user")
    wallet = relationship("Wallet", uselist=False, back_populates="user")
    bookings = relationship("Booking", back_populates="user")