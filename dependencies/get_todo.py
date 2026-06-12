from typing import Annotated
from fastapi import HTTPException
from fastapi.params import Depends
from CRUD.todo_crud import get_todo_by_id_db
from dependencies.db import DBSession
from models import Todo


def get_todo_by_id(todo_id: int,
                   session : DBSession) -> Todo:
    todo = get_todo_by_id_db(session,todo_id)
    if not todo:
        raise HTTPException(status_code=404)
    return todo


TodoOr404 = Annotated[
    Todo,
    Depends(get_todo_by_id)
]