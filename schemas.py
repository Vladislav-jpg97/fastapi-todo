from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TodoBase(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    description: str | None = Field(max_length=1024)
    completed: bool = Field(default=False)
    deadline: datetime


class TodoCreate(TodoBase):
    pass

class TodoUpdate(TodoBase):
    pass

class TodoRead(TodoBase):
    id: UUID

class TodoModify(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    completed: bool | None = None
    deadline: datetime | None = None
