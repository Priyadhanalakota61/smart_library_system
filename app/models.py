from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = 'books'
    __table_args__ = (CheckConstraint('total_copies > 0'),
                     CheckConstraint('available_copies >= 0 AND available_copies <= total_copies'),
                     {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'})
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    total_copies: Mapped[int] = mapped_column(Integer)
    available_copies: Mapped[int] = mapped_column(Integer)


class Member(Base):
    __tablename__ = 'members'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class Loan(Base):
    __tablename__ = 'loans'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id'), index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
