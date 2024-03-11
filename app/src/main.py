import os

from dotenv import load_dotenv
from fastapi import FastAPI

from src.models.user import User
from src.services.mongo_service import MongoService

app = FastAPI()

load_dotenv()
db_manager = os.getenv("DB_MANAGER")
if db_manager == "mongo":
    db_service = MongoService(os.getenv("MONGO_USER"), os.getenv("MONGO_PASS"))
elif db_manager == "mariadb":
    pass
else:
    raise ValueError(f"Invalid DB_MANAGER: {db_manager}")


@app.get("/")
async def root():
    return {"is_alive": db_service.is_alive()}


"""
    Users
"""


@app.get("/users")
async def get_users() -> list[User]:
    return db_service.get_users()


@app.get("/users/{user_id}")
async def get_user(user_id: str) -> User | dict:
    res = db_service.get_user(user_id)
    if res:
        return res
    else:
        return {"error": "User not found"}


@app.post("/users")
async def create_user(user: User) -> User | dict:
    res = db_service.create_user(user)
    if res:
        return res
    else:
        return {"error": "Email already registered"}


@app.delete("/users/{user_id}")
async def delete_user(user_id: str) -> User | dict:
    res = db_service.delete_user(user_id)
    if res:
        return {"message": "User deleted"}
    else:
        return {"error": "User not found"}


@app.put("/users/{user_id}")
async def update_user(user_id: str, user: User) -> User | dict:
    res = db_service.update_user(user_id, user)
    if res:
        return res
    else:
        return {"error": "User not found"}


"""
    Tasks
"""


@app.get("/tasks")
async def get_tasks() -> list[Task]:
    pass
