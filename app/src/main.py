import os
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI

from src.models.task import Task, TaskCreate
from src.models.user import User, UserLogin
from src.services.mariadb_service import MariaDBService
from src.services.mongo_service import MongoService

app = FastAPI()

load_dotenv()
db_manager = os.getenv("DB_MANAGER")
if db_manager == "mongo":
    db_service = MongoService(os.getenv("MONGO_USER"), os.getenv("MONGO_PASS"))
elif db_manager == "mariadb":
    db_service = MariaDBService(os.getenv("MARIADB_USER"), os.getenv("MARIADB_PASS"), os.getenv("MARIADB_DATABASE"))
else:
    raise ValueError(f"Invalid DB_MANAGER: {db_manager}")


@app.get("/")
async def root() -> dict:
    return db_service.is_alive()


"""
    Users
"""


@app.get("/users")
async def get_users(token: str) -> list[User] | dict:
    res = db_service.get_users(token)
    if type(res) is list:
        return res
    return {"error": res}


@app.get("/users/{user_id}")
async def get_user(user_id: str, token: str) -> User | dict:
    res = db_service.get_user(user_id, token)
    if type(res) is User:
        return res
    return {"error": res}


@app.post("/users/get_token")
async def get_token(user: UserLogin) -> dict:
    res = db_service.get_token(user)
    if res:
        return {"token": res}
    return {"error": "Invalid credentials"}


@app.post("/users")
async def create_user(user: UserLogin) -> User | dict:
    res = db_service.create_user(user)
    if type(res) is User:
        return res
    return {"error": res}


@app.delete("/users/{user_id}")
async def delete_user(user_id: str, token: str) -> User | dict:
    res = db_service.delete_user(user_id, token)
    if res == True:
        return {"message": "User deleted"}
    return {"error": res}


@app.put("/users/{user_id}")
async def update_user(user_id: str, token: str, user: UserLogin) -> UserLogin | dict:
    res = db_service.update_user(user_id, token, user)
    if type(res) is UserLogin:
        return res
    return {"error": res}


"""
    Tasks
"""


@app.get("/tasks")
async def get_tasks(token: str) -> list[Task] | dict:
    res = db_service.get_tasks(token)
    if type(res) is list:
        return res
    return {"error": res}


@app.get("/tasks/{task_id}")
async def get_task(task_id: UUID, token: str) -> Task | dict:
    res = db_service.get_task(task_id, token)
    if type(res) is Task:
        return res
    return {"error": res}


@app.post("/tasks")
async def create_task(task: TaskCreate, token: str) -> Task | dict:
    res = db_service.create_task(task, token)
    if type(res) is Task:
        return res
    return {"error": res}


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: UUID, token: str) -> Task | dict:
    res = db_service.delete_task(task_id, token)
    if res == True:
        return {"message": "Task deleted"}
    return {"error": res}


@app.put("/tasks/{task_id}")
async def update_task(task_id: UUID, token: str, task: TaskCreate) -> Task | dict:
    res = db_service.update_task(task_id, token, task)
    if type(res) is Task:
        return res
    return {"error": res}


"""
    BUSTER CALL (delete everything)
"""


@app.delete("/buster_call")
async def buster_call(token: str) -> dict:
    res = db_service.delete_data(token)
    if res:
        return {"message": "All data deleted"}
    return {"error": "Unauthorized"}
