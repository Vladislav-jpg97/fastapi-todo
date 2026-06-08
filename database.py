from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5433/TodoApp"
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)
