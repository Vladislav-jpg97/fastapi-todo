from fastapi import APIRouter, HTTPException, status
from dependencies.db import DBSession
from CRUD.user_crud import create_user_db, get_user_by_id_db, get_list_users, delete_user_db, update_user_db
from schemas import UserCreate, UserUpdate

# =====================================================================
# НАСТРОЙКА МАРШРУТИЗАТОРА (Начало любого модуля)
# =====================================================================
# Создаем изолированный роутер для конкретной сущности (в данном случае Users)
router = APIRouter(
    prefix="/users",  # Автоматически добавляет "/users" ко всем путям ниже (меньше дублирования кода!)
    tags=["Users"]  # Группирует эти эндпоинты в красивый отдельный блок в Swagger (/docs)
)


# =====================================================================
# 1. СЦЕНАРИЙ: POST — СОЗДАНИЕ СУЩНОСТИ
# =====================================================================
@router.post(
    "/",  # Благодаря префиксу, полный путь будет: POST /users/
    status_code=status.HTTP_201_CREATED,
    # 🔥 Стандарт для создания. Показывает, что объект именно СОЗДАН (201), а не просто всё ок (200).
    summary="Создать пользователя"  # Красивое короткое описание для документации Swagger
)
def create_user(body: UserCreate, session: DBSession):
    """
    Принимает JSON (body) -> Валидирует его через UserCreate ->
    Передает в CRUD -> Возвращает созданный объект.
    """
    # Мы полностью доверяем CRUD-функции. Она создает пользователя и возвращает его.
    # FastAPI автоматически превратит возвращенный объект SQLAlchemy в JSON-ответ.
    return create_user_db(session, body)


# =====================================================================
# 2. СЦЕНАРИЙ: GET — ПОЛУЧЕНИЕ ОДНОЙ ЗАПИСИ (Деталка с проверкой)
# =====================================================================
@router.get(
    "/{user_id}",  # Переменная в пути. FastAPI автоматически передаст её в функцию как аргумент user_id
    summary="Получить пользователя по ID"
)
def read_user(user_id: int, session: DBSession):
    # Шаг 1: Запрашиваем данные у базы данных
    user = get_user_by_id_db(session, user_id)

    # Шаг 2: Проверка на существование (Главное правило роутера!)
    if user:
        # Если объект найден — собираем и отдаем аккуратный словарь (JSON-ответ)
        return {
            "id": user.id,
            "username": user.username,
            "todos": user.todos,
            "profile": user.profile
        }

    # Шаг 3: Если CRUD вернул None — прерываем выполнение и кидаем HTTP-ошибку.
    # Клиент увидит статус 404 Not Found и наше сообщение. Код ниже этой строчки не выполнится.
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


# =====================================================================
# 3. СЦЕНАРИЙ: GET — ПОЛУЧЕНИЕ СПИСКА (Трансформация данных / Маппинг)
# =====================================================================
@router.get(
    "/",  # Полный путь: GET /users/
    summary="Список пользователей"
)
def list_users(session: DBSession):
    """
    Шаблон для построения сложных ответов.
    Иногда объекты из БД нельзя отдавать "как есть" (например, там есть пароли),
    или фронтенду нужен специфический формат JSON.
    """
    # Шаг 1: Выкачиваем список объектов из базы
    users_list = get_list_users(session)

    # Шаг 2: Вручную трансформируем список объектов в структуру JSON (List comprehension)
    # Это гарантирует, что мы отдадим только те поля, которые планировали, и в нужном виде.
    return [
        {
            "user_id": user.id,
            "username": user.username,
            # Тернарный оператор (if/else) защищает от падения, если у юзера нет профиля (None)
            "profile": {"id": user.profile.id, "bio": user.profile.bio} if user.profile else None,
            # Вложенный генератор для сборки списка задач этого пользователя
            "todos": [
                {
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "completed": todo.completed,
                    "deadline": todo.deadline,
                    # Глубокий вложенный генератор для сборки тегов каждой задачи
                    "tags": [{"id": tag.id, "name": tag.name} for tag in todo.tags]
                }
                for todo in user.todos
            ]
        }
        for user in users_list
    ]


# =====================================================================
# 4. СЦЕНАРИЙ: DELETE — УДАЛЕНИЕ СУЩНОСТИ
# =====================================================================
@router.delete(
    "/{user_id}",  # Полный путь: DELETE /users/{user_id}
    summary="Удаление пользователя"
)
def delete_user(session: DBSession, user_id: int):
    # Шаг 1: Передаем ID в базу данных для удаления
    updated_users_list = delete_user_db(session, user_id)

    # Шаг 2: Проверяем, было ли что удалять.
    # Наша CRUD-функция возвращает None, если юзера не существовало.
    if updated_users_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Шаг 3: Если всё ок, возвращаем свежий список пользователей (фронтенд сразу обновит интерфейс)
    return updated_users_list


# =====================================================================
# 5. СЦЕНАРИЙ: PATCH — ЧАСТИЧНОЕ ОБНОВЛЕНИЕ
# =====================================================================
@router.patch(
    "/{user_id}",  # Полный путь: PATCH /users/{user_id}
    summary="Изменение пользователя"
)
def update_user(session: DBSession, user_id: int, body: UserUpdate):
    """
    PATCH используется для частичного изменения полей (например, поменять только username).
    body проверяется Pydantic-схемой UserUpdate.
    """
    # Шаг 1: Передаем данные в CRUD на обновление
    user = update_user_db(session, user_id, body)

    # Шаг 2: Проверяем результат
    if user:
        # Возвращаем аккуратный ответ с подтверждением
        return {"user_name": user.username}

    # Шаг 3: Защита. Если ID не подошел — отдаем 404
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")