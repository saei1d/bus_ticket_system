# app/models/profile.py
from .base_imports import Base, Column, Integer, String, ForeignKey, relationship

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # passenger, operator, admin
    full_name = Column(String(100))

    user = relationship("User", back_populates="profiles")