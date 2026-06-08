from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Базовый класс Моделек
class Base(DeclarativeBase):
    pass

#Моделька
class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    title: Mapped[str] = mapped_column(String(255),nullable=False)
    description : Mapped[str] = mapped_column(nullable=True)
    completed: Mapped[bool] = mapped_column(default=False)
    deadline: Mapped[datetime] = mapped_column(nullable=False)

