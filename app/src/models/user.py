from uuid import UUID

from pydantic import BaseModel

from src.models.task import Task


class User(BaseModel):
    id: str
    password: str
    uuid: UUID
    tasks: list[Task] = []


class UserLogin(BaseModel):
    id: str
    password: str
