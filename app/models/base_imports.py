# app/models/base_imports.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, func, text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base