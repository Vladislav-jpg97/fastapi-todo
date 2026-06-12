from datetime import datetime
from sqlalchemy import String, ForeignKey, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# =====================================================================
# БАЗОВЫЙ КЛАСС (Точка старта для миграций Alembic)
# =====================================================================
class Base(DeclarativeBase):
    """
    Диспетчер метаданных. Когда ты будешь создавать миграции,
    Alembic будет смотреть именно сюда, чтобы понять, какие таблицы нужно создать в БД.
    """
    pass


# =====================================================================
# СВЯЗЬ ТИПА Many-to-Many (Многие-ко-Многим) — ТАБЛИЦА-МОСТ
# =====================================================================
# Шаблон для: Тегов на статьях, Актеров в фильмах, Студентов на курсах.
# Эта таблица физически создается в БД, но у нее нет своей ORM-модели (класса).
todo_tag = Table(
    "todo_tag",
    Base.metadata,
    # primary_key=True на обоих полях создает "составной первичный ключ".
    # Это гарантирует, что нельзя привязать один и тот же тег к одной задаче дважды.
    # ondelete="CASCADE" — важнейший дворник. Стирает связи, если удален сам Todo или Tag.
    Column("todo_id", ForeignKey("todos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)


# =====================================================================
# СУЩНОСТЬ: ПОЛЬЗОВАТЕЛЬ (Главный родитель)
# =====================================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(320), unique=True)

    # 🔗 СВЯЗЬ №1: Один-ко-Многим (One-to-Many) -> Возвращает СПИСОК [list]
    # На стороне родителя relationship всегда объявляется как список объектов: list["Todo"].
    # back_populates="user" — это синхронизатор. Он говорит: "Если ты заглянешь в модель Todo,
    # там автора этой задачи будет хранить переменная с именем 'user'".
    todos: Mapped[list["Todo"]] = relationship(back_populates="user")

    # 🔗 СВЯЗЬ №2: Один-к-Одному (One-to-One) -> Возвращает ОДИН объект
    # На стороне родителя пишется строго тип одной модели: "Profile".
    # Чтобы связь была честной 1:1, в дочерней таблице на ForeignKey ставится ограничение unique=True,
    # либо SQLAlchemy сама поймет это, если тип данных указан не как list.
    profile: Mapped["Profile"] = relationship(back_populates="user")


# =====================================================================
# СУЩНОСТЬ: ЗАДАЧА (Младший потомок сущности User)
# =====================================================================
class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255),
                                       nullable=False)  # nullable=False — жесткое требование на уровне СУБД
    description: Mapped[str] = mapped_column(nullable=True)  # nullable=True — база разрешает записывать NULL (None)
    completed: Mapped[bool] = mapped_column(default=False)  # default задает дефолтное значение для новых строк
    deadline: Mapped[datetime] = mapped_column(nullable=False)

    # 🔒 ХРАНИЛИЩЕ СВЯЗИ (Реальная колонка в таблице)
    # user_id — это физический столбец типа INTEGER. Он хранит число (ID владельца).
    # ForeignKey указывает СУБД проверять: "Если мы пишем сюда user_id=5, то в таблице users ОБЯЗАН быть юзер с id=5".
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # ✨ ВИРТУАЛЬНОЕ ПОЛЕ (Фичи ORM, которых нет в обычном SQL)
    # Поле 'user' физически не существует в таблице 'todos' внутри базы данных.
    # Оно нужно только Python, чтобы ты мог написать: print(todo.user.username)
    user: Mapped[User] = relationship(back_populates="todos")

    # ✨ ВИРТУАЛЬНОЕ ПОЛЕ МНОГИЕ-КО-МНОГИМ
    # lazy="selectin" — спасение от ленивой загрузки. Когда ты запросишь Todo, SQLAlchemy
    # автоматически сделает быстрый доп-запрос и сразу наполнит список tags актуальными объектами.
    # secondary=todo_tag — принудительно указывает, через какой "мост" соединять таблицы.
    tags: Mapped[list["Tag"]] = relationship(
        lazy="selectin",
        back_populates="todos",
        secondary=todo_tag
    )


# =====================================================================
# СУЩНОСТЬ: ПРОФИЛЬ (Дочерний напарник для User)
# =====================================================================
class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Чтобы связь 1:1 была железной, хорошей практикой считается добавлять unique=True прямо сюда.
    # Но так как ты управляешь созданием через CRUD ( create_user_profile_db ), база защищена твоим кодом.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    bio: Mapped[str] = mapped_column(String(500), nullable=True)

    # Виртуальная ссылка обратно на родителя. Позволяет из профиля достать юзера: profile.user.id
    user: Mapped[User] = relationship(back_populates="profile")


# =====================================================================
# СУЩНОСТЬ: ТЕГ (Самостоятельная сущность для Many-to-Many)
# =====================================================================
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Зеркальное отображение связи Many-to-Many.
    # Позволяет посмотреть, в каких задачах используется данный тег: tag.todos
    todos: Mapped[list["Todo"]] = relationship(
        lazy="selectin",
        back_populates="tags",
        secondary=todo_tag
    )