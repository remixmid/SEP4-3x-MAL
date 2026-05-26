from datetime import datetime

from pydantic import EmailStr
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fullname: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)

class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    pref_temperature: Mapped[float] = mapped_column(Float, nullable=False)
    pref_humidity: Mapped[float] = mapped_column(Float, nullable=False)
    comfort_score: Mapped[float] = mapped_column(Float, nullable=False)

    source: Mapped[str] = mapped_column(String(50), default="model", nullable=False)
    applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    current_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_humidity: Mapped[float | None] = mapped_column(Float, nullable=True)

    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_weekend: Mapped[int | None] = mapped_column(Integer, nullable=True)

    feedback_items: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )


class Feedback(Base):
    __tablename__ = "feedback"

    __table_args__ = (
        UniqueConstraint(
            "scenario_id",
            "indicator",
            name="uq_feedback_scenario_indicator",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenarios.id"),
        nullable=False,
        index=True,
    )

    indicator: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    liked: Mapped[bool] = mapped_column(Boolean, nullable=False)

    scenario: Mapped[Scenario] = relationship(
        "Scenario",
        back_populates="feedback_items",
    )

