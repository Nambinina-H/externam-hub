from datetime import datetime

from sqlalchemy import Boolean, DateTime, func, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.modules.users.enums import UserRoleEnum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    firstname: Mapped[str] = mapped_column(String(100))
    lastname: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(150), default="", nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), default="", nullable=True)
    role: Mapped[str] = mapped_column(String(50), default=UserRoleEnum.USER.value)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
