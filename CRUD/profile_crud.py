from sqlalchemy import select
from sqlalchemy.orm import Session
from models import User, Profile
from schemas import ProfileUpdate


# =====================================================================
# 1. СЦЕНАРИЙ: READ — ПОЛУЧЕНИЕ ПРОФИЛЯ ПО РОДИТЕЛЬСКОМУ ID
# =====================================================================
def get_user_profile_db(session: Session, user_id: int) -> Profile | None:
    """
    Ищет профиль в таблице 'profiles', используя внешний ключ (user_id).
    Шаблон для: Поиска любых дочерних данных, зная ID родителя.
    """
    # Пишем SQL-запрос: "Выбрать всё из таблицы Profile, где поле user_id совпадает с переданным"
    stmt = select(Profile).where(Profile.user_id == user_id)

    # Выполняем и возвращаем ОДИН объект или None, если профиля (или юзера) нет
    return session.execute(stmt).scalar_one_or_none()


# =====================================================================
# 2. СЦЕНАРИЙ: UPDATE — ОБНОВЛЕНИЕ С ПРЕДВАРИТЕЛЬНЫМ ПОИСКОМ
# =====================================================================
def update_user_profile_db(session: Session, user_id: int, body: ProfileUpdate) -> Profile | None:
    """
    Обновляет данные существующего профиля.
    Шаблон для: Редактирования дочерних записей (изменение настроек, деталей).
    """
    # Шаг 1: Переиспользуем функцию поиска, которую написали чуть выше.
    # Зачем дублировать код select, если можно вызвать get_user_profile_db?
    profile = get_user_profile_db(session, user_id)

    # Шаг 2: Если профиль не найден, возвращаем None (сигнал роутеру выдать 404)
    if not profile:
        return None

    # Шаг 3: Перезаписываем поле bio новыми данными из Pydantic-тела (body)
    profile.bio = body.bio

    # Шаг 4: Фиксируем изменения в базе данных
    session.commit()

    # Шаг 5: Перечитываем объект, чтобы внутри него были самые свежие данные из БД
    session.refresh(profile)
    return profile


# =====================================================================
# 3. СЦЕНАРИЙ: CREATE — СОЗДАНИЕ С ДВОЙНОЙ ЗАЩИТОЙ (Связь 1:1)
# =====================================================================
def create_user_profile_db(session: Session, user_id: int, body: ProfileUpdate) -> Profile | str:
    """
    Создает профиль для пользователя, проходя жесткие бизнес-проверки.
    Шаблон для: Любых связей 1:1, где нельзя плодить дубликаты (например, создание одного кошелька для аккаунта).
    """
    # ЗАЩИТА №1: Проверяем, существует ли вообще родитель (User).
    # Нельзя создать профиль для несуществующего человека — база данных упадет из-за ForeignKey.
    user = session.get(User, user_id)
    if not user:
        return "user_not_found"  # Текстовый маркер (флаг) для роутера

    # ЗАЩИТА №2: Проверяем, нет ли у этого юзера УЖЕ созданного профиля.
    # Так как связь 1:1, у пользователя может быть строго ОДИН профиль.
    stmt = select(Profile).where(Profile.user_id == user_id)
    existing_profile = session.execute(stmt).scalar_one_or_none()
    if existing_profile:
        return "profile_already_exists"  # Еще один флаг для роутера

    # Шаг 3: Если обе проверки прошли успешно — создаем профиль
    new_profile = Profile(
        user_id=user_id,
        bio=body.bio
    )

    session.add(new_profile)  # Добавляем в сессию
    session.commit()  # Фиксируем в БД
    session.refresh(new_profile)  # Обновляем объект
    return new_profile


# =====================================================================
# 4. СЦЕНАРИЙ: DELETE — УДАЛЕНИЕ ДОЧЕРНЕЙ ЗАПИСИ
# =====================================================================
def delete_user_profile_db(session: Session, user_id: int) -> bool:
    """
    Ищет профиль пользователя и полностью удаляет его из базы.
    Шаблон для: Изолированного удаления под-ресурсов (удалить анкету, но оставить юзера).
    """
    # Шаг 1: Ищем профиль по user_id
    stmt = select(Profile).where(Profile.user_id == user_id)
    profile = session.execute(stmt).scalar_one_or_none()

    # Шаг 2: Если удалять нечего — возвращаем False (роутер кинет 404)
    if not profile:
        return False

    # Шаг 3: Удаляем запись и сохраняем транзакцию
    session.delete(profile)
    session.commit()

    # Шаг 4: Возвращаем True — знак успешного удаления
    return True