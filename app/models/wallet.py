# app/models/wallet.py
from .base_imports import Base, Column, Integer, ForeignKey, Numeric, relationship

class Wallet(Base):
    __tablename__ = "wallets"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    balance = Column(Numeric(14, 2), default=0.0, nullable=False)

    user = relationship("User", back_populates="wallet")