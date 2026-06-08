from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, insert

from database import engine
from models import Todo
from schemas import TodoCreate, TodoUpdate


def create_todo_db(new_todo: TodoCreate):
    with Session(engine) as session:
        # Высокоуровневый вариант
        todo = Todo(
            title=new_todo.title,
            description=new_todo.description,
            completed=new_todo.completed,
            deadline=new_todo.deadline,
        )
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


def get_todo_by_id_db(todo_id: int):
    with Session(engine) as session:
        # Высокоуровневый вариант
        # todo = session.get(Todo , todo_id)
        # return todo

        # низкоуровневый вариант
        stmt = select(Todo).where(Todo.id == todo_id)
        result = session.execute(stmt)
        todo: Todo | None = result.scalar_one_or_none()
        return todo


def update_todo_db(todo: Todo, body: TodoUpdate):
    with Session(engine) as session:
        # высокоуровневый
        # todo.title = body.title
        # todo.description = body.description
        # todo.completed = body.completed
        # todo.deadline = body.deadline

        # низкоуровневый
        stmt = update(Todo).values(
            title=body.title,
            description=body.description,
            completed=body.completed,
            deadline=body.deadline,
        ).where(Todo.id == todo.id)
        session.execute(stmt)
        session.commit()


def delete_todo_db(todo: Todo):
    with Session(engine) as session:
        # высокоуровневая
        session.delete(todo)
        session.commit()

        # низкоуровневый
        stmt = delete(Todo).where(Todo.id == todo.id)
        session.execute(stmt)
        session.commit()


def list_todo_db(
        q: str | None = None,
        is_completed: bool | None = None,
        deadline_start: datetime | None = None,
        deadline_end: datetime | None = None
):
    with Session(engine) as session:
        stmt = select(Todo)

        if q is not None:
            stmt = stmt.where(
                Todo.title.like(f"%{q}%")
            )

        if is_completed is not None:
            stmt = stmt.where(
                Todo.completed == is_completed
            )
        if deadline_start is not None:
            stmt = stmt.where(
                Todo.deadline >= deadline_start
            )

        if deadline_end is not None:
            stmt = stmt.where(
                Todo.deadline <= deadline_end
            )

        stmt = stmt.order_by(Todo.title.asc())
        todos_from_db = session.scalars(stmt).all()
        return todos_from_db

# дз1
def complete_todo_db(todo: Todo):
    with Session(engine) as session:
        session.add(todo)
        todo.completed = True
        session.commit()
        session.refresh(todo)
        return todo

# дз2
def modify_todo_db(todo: Todo, patch_data):
    with Session(engine) as session:
        session.add(todo)
        todo.title = patch_data.title if patch_data.title is not None else todo.title
        todo.description = patch_data.description if patch_data.description is not None else todo.description
        todo.completed =  patch_data.completed if patch_data.completed is not None else todo.completed
        todo.deadline =  patch_data.deadline if patch_data.deadline is not None else todo.deadline
        session.commit()
        session.refresh(todo)
        return todo

