from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from database import engine


def get_db():
    try:
        with Session(engine) as session:
            yield session
    finally:
        session.close()

DBSession = Annotated[
    Session,
    Depends(get_db)
]

