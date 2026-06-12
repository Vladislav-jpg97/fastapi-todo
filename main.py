from schemas import TodoRead

import importlib
import pkgutil
from fastapi import FastAPI
import routers  # Импортируем саму папку (пакет) с роутерами

app = FastAPI()
TODOS: list[TodoRead] = []

# Автоматическое подключение всех роутеров из папки
for _, module_name, _ in pkgutil.iter_modules(routers.__path__):
    # Динамически импортируем каждый файл (например, 'routers.todo', 'routers.users')
    module = importlib.import_module(f"routers.{module_name}")

    # Проверяем, есть ли внутри файла переменная 'router'
    if hasattr(module, "router"):
        app.include_router(module.router)
        print(f" Найдено и подключено: routers.{module_name}")

# if __name__ == "__main__":
#     Base.metadata.create_all(
#         bind = engine
#     )
