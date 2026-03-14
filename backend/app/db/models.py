from typing import List, Literal
from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, DateTime, func, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    login: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    pass_hash: Mapped[str] = mapped_column(String)

    role: Mapped[Literal["admin", "user"]] = mapped_column(String, default="user")

    videos: Mapped[List["VideoInstance"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class VideoInstance(Base):
    __tablename__ = "video_instances"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    name: Mapped[str] = mapped_column(String(100))
    initial_name: Mapped[str] = mapped_column(String, default=name)
    status: Mapped[Literal["stopped", "in_queue", "in_progress", "done", "error"]] = (
        mapped_column(String, default="stopped"))
    upload_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)

    user: Mapped["User"] = relationship(back_populates="videos")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    token_hash: Mapped[str] = mapped_column(String)
    status: Mapped[Literal["active", "rotated", "revoked"]] = mapped_column(String, default="active")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    replaced_by_token_id: Mapped[int | None] = mapped_column(ForeignKey("refresh_tokens.id"), nullable=True)
    revoke_reason: Mapped[Literal["logout", "banned", "other"] | None] = mapped_column(String, nullable=True)
