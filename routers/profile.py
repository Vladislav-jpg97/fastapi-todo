from fastapi import APIRouter, HTTPException, status
from dependencies.db import DBSession
from CRUD.profile_crud import get_user_profile_db, update_user_profile_db, create_user_profile_db, \
    delete_user_profile_db
from schemas import ProfileUpdate

# =====================================================================
# ИНИЦИАЛИЗАЦИЯ МАРШРУТИЗАТОРА ДЛЯ ПОД-РЕСУРСОВ
# =====================================================================
router = APIRouter(
    prefix="/users",  # Префикс остается "/users", потому что мы работаем внутри контекста пользователя
    tags=["Profiles"]  # Отдельный тег в Swagger, чтобы не перемешивать управление аккаунтом и управление анкетой
)


# =====================================================================
# 1. СЦЕНАРИЙ: POST — СОЗДАНИЕ СВЯЗАННОЙ СУЩНОСТИ (Связь 1:1)
# =====================================================================
@router.post(
    "/{user_id}/profile",
    status_code=status.HTTP_201_CREATED,  # Для успешного создания всегда используем 201
    summary="Создать профиль пользователя"
)
def create_profile(user_id: int, body: ProfileUpdate, session: DBSession):
    """
    Шаблон для создания зависимой сущности.
    Принимает ID родителя из URL и данные ребенка из JSON-тела.
    """
    # Шаг 1: Передаем сессию, ID родителя и Pydantic-тело в CRUD
    result = create_user_profile_db(session, user_id, body)

    # Шаг 2: Обработка текстовых флагов-маркеров (Бизнес-валидация)
    # Так как у нас связь 1:1, мы должны обработать сценарии, в которых база не может создать запись
    if result == "user_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if result == "profile_already_exists":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="У этого пользователя уже есть профиль")

    # Шаг 3: Если проверки пройдены, result — это объект из БД. Собираем красивый ответ.
    return {
        "message": "Профиль успешно создан",
        "user_id": result.user_id,
        "bio": result.bio
    }


# =====================================================================
# 2. СЦЕНАРИЙ: GET — ПОЛУЧЕНИЕ ЗАВИСИМОЙ СУЩНОСТИ
# =====================================================================
@router.get(
    "/{user_id}/profile",
    summary="Посмотреть профиль пользователя"
)
def get_profile(user_id: int, session: DBSession):
    """
    Шаблон для чтения вложенных данных.
    """
    # Шаг 1: Ищем профиль в базе по ID пользователя
    profile = get_user_profile_db(session, user_id)

    # Шаг 2: Если профиль существует — отдаем его поля фронтенду
    if profile:
        return {
            "user_id": profile.user_id,
            "bio": profile.bio
        }

    # Шаг 3: Если профиля (или самого юзера) нет — отдаем 404
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден")


# =====================================================================
# 3. СЦЕНАРИЙ: PATCH — ОБНОВЛЕНИЕ ЗАВИСИМОЙ СУЩНОСТИ
# =====================================================================
@router.patch(
    "/{user_id}/profile",
    summary="Редактировать профиль"
)
def update_profile(user_id: int, body: ProfileUpdate, session: DBSession):
    """
    Шаблон для обновления вложенных данных.
    """
    # Шаг 1: Отправляем запрос на обновление в CRUD.
    # Внутри CRUD сначала отработает поиск, а затем замена полей.
    updated_profile = update_user_profile_db(session, user_id, body)

    # Шаг 2: Если CRUD вернул None (профиль не найден для обновления) — прерываемся
    if not updated_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден")

    # Шаг 3: Возвращаем обновленный JSON
    return {
        "message": "Профиль успешно изменен",
        "user_id": updated_profile.user_id,
        "bio": updated_profile.bio
    }


# =====================================================================
# 4. СЦЕНАРИЙ: DELETE — УДАЛЕНИЕ ЗАВИСИМОЙ СУЩНОСТИ
# =====================================================================
@router.delete(
    "/{user_id}/profile",
    summary="Удалить профиль пользователя"
)
def delete_profile(user_id: int, session: DBSession):
    """
    Шаблон для изолированного удаления дочерней записи.
    Стирает только профиль, при этом сам Пользователь остается в базе.
    """
    # Шаг 1: CRUD пытается удалить запись и возвращает True (успех) или False (не найдено)
    success = delete_user_profile_db(session, user_id)

    # Шаг 2: Проверяем статус удаления
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден")

    # Шаг 3: Отдаем текстовое подтверждение
    return {"message": "Профиль успешно удален"}