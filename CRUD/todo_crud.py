from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Todo, Tag, todo_tag
from schemas import TodoCreate, TodoUpdate, TodoModify


# =====================================================================
# 1. СЦЕНАРИЙ: CREATE — СОЗДАНИЕ ОБЪЕКТА С ВНЕШНИМ КЛЮЧОМ (POST)
# =====================================================================
def create_todo_db(session: Session, new_todo: TodoCreate) -> Todo:
    """
    Принимает валидированные Pydantic-данные, перекладывает их в модель SQLAlchemy и сохраняет.
    Шаблон для: Создания сущностей, привязанных к родителю (Товар в категории, Комментарий к посту).
    """
    # Шаг 1: Разворачиваем Pydantic-схему в конструктор модели SQLAlchemy
    todo = Todo(
        title=new_todo.title,
        description=new_todo.description,
        completed=new_todo.completed,
        deadline=new_todo.deadline,
        user_id=new_todo.user_id,  # Физическая привязка к Foreign Key родителя
    )
    # Шаг 2: Добавляем в транзакцию, сохраняем в базу и обновляем объект, чтобы получить его id
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


# =====================================================================
# 2. СЦЕНАРИЙ: READ — КЛАССИЧЕСКИЙ ПОИСК ПО ID (GET)
# =====================================================================
def get_todo_by_id_db(session: Session, todo_id: int) -> Todo | None:
    """
    Базовый поиск одной строки по её первичному ключу (Primary Key).
    Шаблон для: Любого эндпоинта детальной информации.
    """
    stmt = select(Todo).where(Todo.id == todo_id)
    result = session.execute(stmt)
    return result.scalar_one_or_none()


# =====================================================================
# 3. СЦЕНАРИЙ: UPDATE — ПОЛНОЕ ОБНОВЛЕНИЕ ЧЕРЕЗ СВОЙСТВА ОБЪЕКТА (PUT)
# =====================================================================
def update_todo_db(session: Session, todo: Todo, body: TodoUpdate) -> Todo:
    """
    Перезаписывает абсолютно все поля существующего объекта.
    Шаблон для: Логики полного обновления (PUT).

    🔥 АРХИТЕКТУРНЫЙ СЕКРЕТ: Мы не используем конструкцию session.execute(update(...)).
    Вместо этого мы меняем атрибуты у живого ORM-объекта `todo.title = ...`.
    Это заставляет SQLAlchemy отслеживать изменения (Unit of Work), автоматически
    синхронизировать локальный кэш памяти и беречь связанные с задачей теги от поломок.
    """
    todo.title = body.title
    todo.description = body.description
    todo.completed = body.completed
    todo.deadline = body.deadline

    session.commit()
    session.refresh(todo)
    return todo


# =====================================================================
# 4. СЦЕНАРИЙ: DELETE — УМНОЕ КАСКАДНОЕ УДАЛЕНИЕ С ОЧИСТКОЙ ХВОСТОВ
# =====================================================================
def delete_todo_db(session: Session, todo: Todo) -> None:
    """
    Удаляет объект и автоматически зачищает "осиротевшие" сущности в Many-to-Many.
    Шаблон для: Удаления сущностей с тегами, категориями или файлами, чтобы база не забивалась мусором.
    """
    # Шаг A: Запоминаем ID всех тегов, которые СЕЙЧАС привязаны к этой задаче.
    # Делаем это до удаления, иначе потом мы потеряем к ним доступ.
    tag_ids_to_check = [tag.id for tag in todo.tags]

    # Шаг B: Командуем сессии удалить саму задачу.
    # Наш внешний ключ в БД настроен как ondelete="CASCADE", поэтому база данных
    # автоматически вычистит строчки из таблицы-моста `todo_tag`.
    session.delete(todo)

    # Сбрасываем изменения в память СУБД (но не коммитим транзакцию!).
    # Теперь в таблице-мосте связей больше нет, и мы можем проверить теги на "одиночество".
    session.flush()

    # Шаг C: Бежим по сохраненным ID тегов и проверяем, привязаны ли они еще хоть к кому-то
    for tag_id in tag_ids_to_check:
        # Пишем запрос к таблице-мосту: "Есть ли хоть одна запись с этим tag_id?"
        stmt = select(todo_tag).where(todo_tag.c.tag_id == tag_id)
        remaining_links = session.execute(stmt).all()

        # Если список связей пуст (remaining_links == []) — значит, этот тег больше никому не нужен!
        if not remaining_links:
            global_tag = session.get(Tag, tag_id)
            if global_tag:
                session.delete(global_tag)  # Удаляем сам тег из глобального справочника `tags`

    # Шаг D: Завершаем транзакцию. Либо удалится ВСЁ (задача + осиротевшие теги), либо ничего, если произойдет сбой.
    session.commit()
    # Очищаем кэш сессии, чтобы при следующем запросе SQLAlchemy гарантированно взяла свежие данные из БД
    session.expire_all()


# =====================================================================
# 5. СЦЕНАРИЙ: READ — ПОЛУЧЕНИЕ СПИСКА С ДИНАМИЧЕСКИМ КОНСТРУКТОРОМ
# =====================================================================
def list_todo_db(
        session: Session,
        q: str | None = None,
        is_completed: bool | None = None,
        deadline_start: datetime | None = None,
        deadline_end: datetime | None = None,
) -> list[Todo]:
    """
    Конструирует SQL-запрос на лету в зависимости от того, какие фильтры передал клиент.
    Шаблон для: Поисковых движков, сложных фильтров в каталогах, админ-панелей.
    """
    # Шаг 1: Задаем базовый "чистый" запрос
    stmt = select(Todo)

    # Шаг 2: Динамически модифицируем переменную запроса (перезаписываем stmt новым условием)
    if q is not None:
        # Поиск по подстроке (SQL оператор LIKE). Ищет совпадение в любой части названия.
        stmt = stmt.where(Todo.title.like(f"%{q}%"))

    if is_completed is not None:
        # Фильтр по строгому равенству (True/False)
        stmt = stmt.where(Todo.completed == is_completed)

    if deadline_start is not None:
        # Фильтр "От" (больше или равно)
        stmt = stmt.where(Todo.deadline >= deadline_start)

    if deadline_end is not None:
        # Фильтр "До" (меньше или равно)
        stmt = stmt.where(Todo.deadline <= deadline_end)

    # Шаг 3: Навешиваем сортировку по алфавиту от А до Я (.asc())
    stmt = stmt.order_by(Todo.title.asc())

    # Шаг 4: Выполняем итоговый собранный SQL-запрос
    return list(session.scalars(stmt).all())


# =====================================================================
# 6. СЦЕНАРИЙ: PATCH — АТОМАРНЫЙ ЭКШЕН (Быстрое переключение флага)
# =====================================================================
def complete_todo_db(session: Session, todo: Todo) -> Todo:
    """
    Шаблон для быстрых точечных действий (RPC-стиль).
    Используется, когда эндпоинт делает ровно ОДНО конкретное действие (Закрыть заказ, Опубликовать пост).
    """
    todo.completed = True  # Просто переводим флаг в True
    session.commit()
    session.refresh(todo)
    return todo


# =====================================================================
# 7. СЦЕНАРИЙ: PATCH — ДИНАМИЧЕСКОЕ ЧАСТИЧНОЕ ОБНОВЛЕНИЕ
# =====================================================================
def modify_todo_db(session: Session, todo: Todo, patch_data: TodoModify) -> Todo:
    """
    Обновляет ТОЛЬКО те поля, которые клиент прислал в JSON-теле запроса.
    Шаблон для: Идеального PATCH-метода в REST API.
    """
    # Шаг 1: Важнейший метод Pydantic. `exclude_unset=True` превращает схему в словарь,
    # выкидывая оттуда все дефолтные None, которые клиент НЕ присылал.
    # Если клиент прислал только {"title": "Новое имя"}, в update_data будет ровно один этот ключ.
    update_data = patch_data.model_dump(exclude_unset=True)

    # Шаг 2: Бежим по словарю присланных полей
    for key, value in update_data.items():
        # Встроенная функция Python setattr(объект, "имя_поля", значение)
        # делает то же самое, что и: todo.title = "Новое имя"
        setattr(todo, key, value)

    # Шаг 3: Сохраняем и обновляем объект
    session.commit()
    session.refresh(todo)
    return todo