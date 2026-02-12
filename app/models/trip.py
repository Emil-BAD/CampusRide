from sqlalchemy import String, Integer, Text, Date, Time, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Trip(Base):
    """Поездка — данные из create_trip"""
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type_trip: Mapped[str] = mapped_column(String(20), nullable=False)  # personal_ts | taxi_ts
    point_from_id: Mapped[int] = mapped_column(ForeignKey("dorms.id", ondelete="RESTRICT"), nullable=False)
    point_to_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="RESTRICT"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    time: Mapped[Time] = mapped_column(Time, nullable=False)
    quantity_places: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active | completed | cancelled
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creator: Mapped["User"] = relationship("User", back_populates="created_trips")
    point_from: Mapped["Dorm"] = relationship("Dorm", back_populates="trips_from")
    point_to: Mapped["Building"] = relationship("Building", back_populates="trips_to")
    participants: Mapped[list["TripParticipant"]] = relationship("TripParticipant", back_populates="trip")


class TripParticipant(Base):
    """Участники поездки (связь user ↔ trip)"""
    __tablename__ = "trip_participants"
    __table_args__ = (UniqueConstraint("trip_id", "user_id", name="uq_trip_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trip: Mapped["Trip"] = relationship("Trip", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="participations")
