
from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import JSONResponse

from crud import create_todo_db, get_todo_by_id_db, update_todo_db, delete_todo_db, list_todo_db, complete_todo_db, \
    modify_todo_db
from database import engine
from models import Base
from schemas import TodoCreate, TodoUpdate, TodoRead, TodoModify

app = FastAPI()

TODOS: list[TodoRead] = []


# это схема или моделька pydantic
class Item(BaseModel):
    name: str
    description: str
    price: float
    is_active: bool


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.post("/items")
def create_item(item: Item):
    return item


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, q: str | None = None):
    return {"item_id": item_id, "item": item}


@app.post(
    "/todos",
    status_code=201,
    summary="Создание задачи",
    description="Базовое создание задачи без БД",
    response_model=TodoRead,
)
def create_todo(
        new_todo: TodoCreate
):
    # todo = TodoRead(
    #     id=uuid.uuid4(),
    #     name=new_todo.name,
    #     description=new_todo.description,
    #     deadline=new_todo.deadline,
    #     completed=new_todo.completed,
    # )
    # TODOS.append(
    #     todo
    # )
    todo = create_todo_db(new_todo)

    return todo


@app.put(
    "/todos/{todo_id}",
    summary="Обновление задачи",
    status_code=204
)
def update_todo(
        todo_id: int,
        updated_todo: TodoUpdate
):
    # for index, todo in enumerate(TODOS):
    #     if todo.id == todo_id:
    #         TODOS[index] = TodoRead(
    #             id=todo.id,
    #             title=updated_todo.title,
    #             description=updated_todo.description,
    #             deadline=updated_todo.deadline,
    #             completed=updated_todo.completed,
    #         )
    #         return None
    todo = get_todo_by_id_db(todo_id)
    if todo:
        update_todo_db(todo,updated_todo)
        return None
    return JSONResponse(
        status_code=404,
        content={
            "message": "Todo Not Found"
        }
    )


@app.delete("/todos/{todo_id}")
def delete_item(todo_id: int):
    todo = get_todo_by_id_db(todo_id)
    if todo:
        delete_todo_db(todo)
    raise HTTPException(
        status_code=404,
        detail={
            "message": "Todo Not Found"
        }
    )


@app.get("/todos/{todo_id}")
def read_todo(todo_id: int):
    # for index, todo in enumerate(TODOS):
    #     if todo.id == todo_id:
    #         return todo
    # raise HTTPException(
    #     status_code=404,
    #     detail={
    #         "message": "Todo Not Found"
    #     }
    # )
    todo = get_todo_by_id_db(todo_id)
    if todo:
        return todo
    raise HTTPException(
        status_code=404,
            detail={
                "message": "Todo Not Found"
            }
        )


@app.get("/todos")
def list_todos(
        q: str | None = None,
        is_completed: bool | None = None,
        deadline_start: datetime | None = None,
        deadline_end: datetime | None = None
):
    todos = TODOS

    # if q is not None:
    #     todos = list(filter(lambda todo: q in todo.name, todos))
    #
    # if is_completed is not None:
    #     todos = list(filter(lambda todo: todo.completed == is_completed, todos))
    #
    # if deadline_start is not None:
    #     deadline_start = deadline_start.replace(tzinfo=timezone.utc)
    #     todos = list(filter(lambda todo: todo.deadline >= deadline_start, todos))
    #
    # if deadline_end is not None:
    #     deadline_end = deadline_end.replace(tzinfo=timezone.utc)
    #     todos = list(filter(lambda todo: todo.deadline <= deadline_end, todos))
    #
    # return todos

    todos = list_todo_db(
        q=q,
        is_completed=is_completed,
        deadline_start=deadline_start,
        deadline_end=deadline_end
    )
    return todos


# эндпоинт делает определенную todo выполненым

@app.patch("/todos/{todo_id}/complete", response_model=TodoRead)
def complete_todo(todo_id: int):
    # for todo in TODOS:
    #     if todo.id == todo_id:
    #         todo.completed = True
    #         return todo
    todo = get_todo_by_id_db(todo_id)
    if todo:
        updated_todo = complete_todo_db(todo)
        return updated_todo
    raise HTTPException(
        status_code=404,
        detail={"message": "Todo Not Found"}
    )


@app.patch("/todos/{todo_id}",
           status_code=200,
           summary="Для частичного обновления ",
           response_model=TodoRead
           )
def modify_todo(
        todo_id: int,
        patch_data : TodoModify
):
    todo = get_todo_by_id_db(todo_id)
    if todo:
        updated_todo = modify_todo_db(todo, patch_data)
        return updated_todo



    # for index, todo in enumerate(TODOS):
    #     if todo.id == todo_id:
    #         new_name = patch_data.title if patch_data.title is not None else todo.title
    #         new_description = patch_data.description if patch_data.description is not None else todo.description
    #         new_completed = patch_data.completed if patch_data.completed is not None else todo.completed
    #         new_deadline = patch_data.deadline if patch_data.deadline is not None else todo.deadline
    #
    #         TODOS[index] = TodoRead(
    #             id=todo.id,
    #             title=new_name,
    #             description=new_description,
    #             completed=new_completed,
    #             deadline=new_deadline
    #         )
    #         return TODOS[index]
    raise HTTPException(
        status_code=404,
        detail={
            "message": "Todo Not Found"
        }
    )



if __name__ == "__main__":
    Base.metadata.create_all(
        bind = engine
    )