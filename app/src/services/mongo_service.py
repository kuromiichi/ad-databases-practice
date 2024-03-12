from datetime import datetime

from pymongo import MongoClient, errors
from uuid import UUID, uuid4

from src.models.task import Task, TaskCreate
from src.models.user import User, UserLogin


root_token = "root"


class MongoService:
    def __init__(self, user, passwd):
        self.client = MongoClient(
            f"mongodb://{user}:{passwd}@mongo:27017", uuidRepresentation="standard"
        )
        self.db = self.client["test"]
        self.users = self.db["users"]
        self.tasks = self.db["tasks"]

    def is_alive(self):
        try:
            self.client.is_primary
            return True
        except errors.ServerSelectionTimeoutError:
            return False

    def get_users(self, token: str) -> list[User] | str:
        if token != root_token:
            return "Unauthorized"
        users = list(self.users.find())
        users_with_tasks = []
        for user in users:
            user = User(**user)
            tasks = list(self.tasks.find({"user_id": user.id}))
            user.tasks = [Task(**task) for task in tasks]
            users_with_tasks.append(user)
        return users_with_tasks

    def get_user(self, user_id: str, token: str) -> User | str:
        if token != root_token:
            return "Unauthorized"
        user = self.users.find_one({"id": user_id})
        if user:
            user = User(**user)
            tasks = list(self.tasks.find({"user_id": user_id}))
            user.tasks = [Task(**task) for task in tasks]
            return user
        return "User not found"

    def get_token(self, user: UserLogin) -> str | None:
        user = self.users.find_one({"id": user.id, "password": user.password})
        if user:
            return str(user["uuid"])
        return None

    def create_user(self, user: UserLogin) -> User | str:
        if self.users.find_one({"id": user.id}):
            return "Email already registered"
        new_user = User(**user.model_dump(), uuid=uuid4())
        self.users.insert_one(new_user.model_dump())
        return new_user

    def delete_user(self, user_id: str, token: str) -> bool | str:
        if token != root_token:
            return "Unauthorized"
        if self.users.find_one({"id": user_id}):
            self.users.delete_one({"id": user_id})
            self.tasks.delete_many({"user_id": user_id})
            return True
        return "User not found"

    def update_user(self, user_id: str, token: str, user: UserLogin) -> UserLogin | str:
        existing_user = self.users.find_one({"id": user_id})
        if existing_user:
            if token != root_token and token != str(existing_user["uuid"]):
                return "Unauthorized"
            self.users.update_one({"id": user_id}, {"$set": user.model_dump()})
            return user
        return "User not found"

    def get_tasks(self, token: str) -> list[Task] | str:
        if token == root_token:
            return list(self.tasks.find())
        try:
            uuid = UUID(token)
        except ValueError:
            return "Invalid token"
        user = self.users.find_one({"uuid": uuid})
        if user:
            return list(self.tasks.find({"user_id": user["id"]}))
        return "Invalid token"

    def get_task(self, task_id: UUID, token: str) -> Task | str:
        task = self.tasks.find_one({"id": task_id})
        if task:
            user_token = self.users.find_one({"id": task["user_id"]})["uuid"]
            if token != root_token and token != str(user_token):
                return "Unauthorized"
            return Task(**self.tasks.find_one({"id": task_id}))
        return "Task not found"

    def create_task(self, task: TaskCreate, token: str) -> Task | str:
        try:
            uuid = UUID(token)
        except ValueError:
            return "Invalid token"
        user = self.users.find_one({"uuid": uuid})
        if user:
            new_task = Task(
                **task.model_dump(),
                id=uuid4(),
                user_id=user["id"],
                created_at=str(datetime.now()),
                updated_at=str(datetime.now()),
            )
            self.tasks.insert_one(new_task.model_dump())
            return new_task
        return "Invalid token"

    def delete_task(self, task_id: UUID, token: str) -> bool | str:
        task = self.tasks.find_one({"id": task_id})
        if task:
            user_token = self.users.find_one({"id": task["user_id"]})["uuid"]
            if token != root_token and token != str(user_token):
                return "Unauthorized"
            self.tasks.delete_one({"id": task_id})
            return True
        return "Task not found"

    def update_task(self, task_id: UUID, token: str, task: TaskCreate) -> Task | str:
        existing_task = self.tasks.find_one({"id": task_id})
        if existing_task:
            user_token = self.users.find_one({"id": existing_task["user_id"]})["uuid"]
            if token != root_token and token != str(user_token):
                return "Unauthorized"
            self.tasks.update_one(
                {"id": task_id},
                {"$set": {**task.model_dump(), "updated_at": str(datetime.now())}},
            )
            return Task(**self.tasks.find_one({"id": task_id}))
        return "Task not found"

    def delete_data(self, token: str) -> bool:
        if token != root_token:
            return False
        self.users.delete_many({})
        self.tasks.delete_many({})
        return True
