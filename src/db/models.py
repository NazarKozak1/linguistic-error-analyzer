from datetime import datetime, UTC
from typing import List
from sqlalchemy import ForeignKey, Text, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Enum, Column, Integer, Date, String
import enum
from datetime import date


class Base(DeclarativeBase):
    """base class for all models."""
    pass


class UserRole(enum.Enum):
    REGULAR = "regular"
    ADMIN = "admin"
    OWNER = "owner"


class User(Base):
    __tablename__ = "users"


    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # original telegram app language
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # language for bot explanations and translations
    preferred_language: Mapped[str] = mapped_column(String(20), default="en")

    # fixed timezone warning using lambda
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    sentences: Mapped[List["Sentence"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # role and limits
    role = Column(Enum(UserRole), default=UserRole.REGULAR, nullable=False)
    daily_requests = Column(Integer, default=0, nullable=False)
    daily_tokens = Column(Integer, default=0, nullable=False)
    last_request_date = Column(Date, default=date.today, nullable=False)




class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    telegram_message_id: Mapped[int] = mapped_column(BigInteger)
    original_text: Mapped[str] = mapped_column(Text)
    corrected_text: Mapped[str] = mapped_column(Text)
    translation: Mapped[str] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    user: Mapped["User"] = relationship(back_populates="sentences")
    errors: Mapped[List["ParsedError"]] = relationship(back_populates="sentence", cascade="all, delete-orphan")


class ParsedError(Base):
    __tablename__ = "parsed_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentences.id"))

    error_fragment: Mapped[str] = mapped_column(Text)
    correction: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
    subcategory: Mapped[str] = mapped_column(String(50))
    cefr_level: Mapped[str] = mapped_column(String(10))
    explanation: Mapped[str] = mapped_column(Text)

    sentence: Mapped["Sentence"] = relationship(back_populates="errors")