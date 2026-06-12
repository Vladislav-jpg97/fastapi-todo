from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dependencies.get_todo import TodoOr404

# Импорт CRUD операций для работы с базой данных
from CRUD.todo_crud import (
    create_todo_db,
    update_todo_db,
    delete_todo_db,
    list_todo_db,
    complete_todo_db,
    modify_todo_db
)
from dependencies.db import DBSession
from models import Todo, Tag, User
from schemas import TodoRead, TodoCreate, TagBase, TodoUpdate, TodoModify

# Инициализация роутера
router = APIRouter(
    prefix="/todos",
    tags=["Todos"]
)


# =====================================================================
# 1. СЦЕНАРИЙ: GET — СПИСОК С ДИНАМИЧЕСКОЙ ФИЛЬТРАЦИЕЙ
# =====================================================================
@router.get(
    "/",
    summary="Получить список задач",
    description="Возвращает список всех задач с возможностью фильтрации по тексту, статусу и дедлайну."
)
def list_todos(
        session: DBSession,
        # Аргументы без фигурных скобок в пути FastAPI автоматически считает Query-параметрами.
        # URL на фронтенде будет выглядеть так: /todos/?q=купить&is_completed=false
        q: str | None = None,
        is_completed: bool | None = None,
        deadline_start: datetime | None = None,
        deadline_end: datetime | None = None,
):
    """
    Шаблон для построения каталогов, поисковых строк и таблиц с фильтрами.
    Вся тяжелая логика сборки SQL-запроса (через if q, if is_completed) уходит в CRUD.
    """
    todos = list_todo_db(
        session,
        q=q,
        is_completed=is_completed,
        deadline_start=deadline_start,
        deadline_end=deadline_end
    )
    return todos


# =====================================================================
# 2. СЦЕНАРИЙ: GET — ПОЛУЧЕНИЕ ПО ID ЧЕРЕЗ ЗАВИСИМОСТЬ
# =====================================================================
@router.get(
    "/{todo_id}",
    summary="Получить задачу по ID"
)
def read_todo(todo: TodoOr404):
    """
    Шаблон идеального эндпоинта. Благодарю тому, что валидация 'есть ли такой ID'
    инкапсулирована (спрятана) в зависимость TodoOr404, тело роутера сократилось до одной строки.
    """
    return todo


# =====================================================================
# 3. СЦЕНАРИЙ: POST — СОЗДАНИЕ С ЗАЩИТОЙ FOREIGN KEY (Внешнего ключа)
# =====================================================================
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED, # Стандарт для успешного создания
    summary="Создание новой задачи",
    response_model=TodoRead, # Гарантирует, что клиенту вернется JSON строго по схеме TodoRead
)
def create_todo(new_todo: TodoCreate, session: DBSession):
    """
    Шаблон создания записи, жестко привязанной к родителю (User -> Todo).
    Перед созданием дочерней записи ОБЯЗАТЕЛЬНО проверяем, существует ли родитель.
    """
    # Защитная проверка: Ищем пользователя, чей ID прислали в теле запроса
    user_exists = session.get(User, new_todo.user_id)
    if not user_exists:
        # Если такого пользователя нет — прерываемся. Иначе база выплюнет ошибку ForeignKey
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"User with id {new_todo.user_id} does not exist. Cannot create todo."}
        )

    # Если пользователь реален — передаем управление в CRUD слой для вставки записи в БД
    todo = create_todo_db(session, new_todo)
    return todo


# =====================================================================
# 4. СЦЕНАРИЙ: PUT — ПОЛНОЕ ОБНОВЛЕНИЕ С КОДОМ 204
# =====================================================================
@router.put(
    "/{todo_id}",
    summary="Полное обновление задачи",
    status_code=status.HTTP_204_NO_CONTENT
    # Статус 204 No Content означает: "Сервер успешно выполнил запрос, но в ответе возвращать нечего".
    # Это частый паттерн для PUT запросов в REST API.
)
def update_todo(
        updated_todo: TodoUpdate,
        session: DBSession,
        todo: TodoOr404 # Зависимость гарантирует, что мы обновляем РЕАЛЬНУЮ задачу
):
    """
    PUT требует, чтобы клиент прислал ВСЕ поля объекта заново для полной перезаписи.
    """
    update_todo_db(session, todo, updated_todo)
    # Возвращать return не нужно, FastAPI сам отдаст пустой ответ со статусом 204


# =====================================================================
# 5. СЦЕНАРИЙ: PATCH — ЧАСТИЧНОЕ ОБНОВЛЕНИЕ (Точечные изменения)
# =====================================================================
@router.patch(
    "/{todo_id}",
    status_code=status.HTTP_200_OK,
    summary="Частичное обновление задачи",
    response_model=TodoRead
)
def modify_todo(patch_data: TodoModify, session: DBSession, todo: TodoOr404):
    """
    PATCH меняет только те поля, которые клиент явно передал в JSON-теле (остальные None).
    """
    # Так как у нас есть TodoOr404, проверка `if todo:` избыточна (зависимость не пропустит None).
    # Но мы оставляем безопасный вызов CRUD-модификатора.
    updated_todo = modify_todo_db(session, todo, patch_data)
    return updated_todo


# =====================================================================
# 6. СЦЕНАРИЙ: DELETE — УДАЛЕНИЕ С ТЕКСТОВЫМ ПОДТВЕРЖДЕНИЕМ
# =====================================================================
@router.delete(
    "/{todo_id}",
    summary="Удаление задачи"
)
def delete_item(session: DBSession, todo: TodoOr404):
    """
    Удаляет объект. В отличие от удаления пользователей (где мы возвращали новый список),
    здесь используется классический паттерн возврата текстового сообщения об успехе.
    """
    delete_todo_db(session, todo)
    return {"message": "Todo successfully deleted"}


# =====================================================================
# 7. СЦЕНАРИЙ: CUSTOM ACTION (Специальное атомарное действие)
# =====================================================================
@router.patch(
    "/{todo_id}/complete",
    summary="Отметить задачу выполненной",
    response_model=TodoRead
)
def complete_todo(session: DBSession, todo: TodoOr404):
    """
    Шаблон для эндпоинтов-действий (RPC-стиль внутри REST).
    Вместо того чтобы слать PATCH /todos/1 с телом {"completed": true},
    клиент просто дергает этот URL без тела, а бэкенд сам знает, что делать.
    """
    updated_todo = complete_todo_db(session, todo)
    return updated_todo


# =====================================================================
# 8. СЦЕНАРИЙ: POST — БЫСТРАЯ ПРИВЯЗКА В MANY-TO-MANY НА МЕСТЕ
# =====================================================================
@router.post(
    "/{todo_id}/tags",
    summary="Добавить тег к задаче"
)
def create_todo_with_tag(todo_id: int, body: TagBase, session: DBSession):
    """
    Этот метод — альтернатива выносу логики в CRUD. Использование сырого кода
    прямо в роутере допустимо для простых связок, но в больших проектах
    этот блок тоже упаковывают в функцию `add_tag_to_todo_db`.
    """
    # Шаг A: Загружаем задачу и сразу подтягиваем связанные теги через selectinload
    stmt = select(Todo).where(Todo.id == todo_id).options(
        selectinload(Todo.tags)
    )
    todo = session.execute(stmt).scalars().one_or_none()

    # Шаг B: Ручная проверка на существование задачи
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Todo with id {todo_id} not found"}
        )

    # Шаг C: Магия SQLAlchemy отношений Many-to-Many.
    # Мы просто делаем .append() нового объекта модели Tag в виртуальный список.
    # SQLAlchemy сама поймет, что нужно пойти и вставить запись в таблицу-мост `todo_tag`.
    todo.tags.append(Tag(name=body.name))

    # Шаг D: Синхронизируем состояние с БД
    session.add(todo)
    session.commit()
    session.refresh(todo)

    # Шаг E: Формируем ответ клиенту
    return {
        "title": todo.title,
        "tags": todo.tags,
    }