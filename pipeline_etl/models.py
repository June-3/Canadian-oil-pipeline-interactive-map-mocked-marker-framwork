"""SQLAlchemy ORM models for Asset and Reading."""

import os
import sys
from datetime import datetime, timezone

# Allow running from project root without PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from pipeline_etl.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # 'sensor' or 'valve'
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="normal")  # normal / warning / alarm
    updated_at = Column(DateTime(timezone=True), nullable=False)

    readings = relationship("Reading", back_populates="asset", cascade="all, delete-orphan")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    temperature = Column(Float, nullable=False)  # Celsius
    pressure = Column(Float, nullable=False)     # PSI

    asset = relationship("Asset", back_populates="readings")


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)
