from pymongo import MongoClient, errors

from src.models.user import User


class MongoService:
    def __init__(self, user, passwd):
        self.client = MongoClient(f"mongodb://{user}:{passwd}@mongo:27017")
        self.db = self.client["test"]
        self.users = self.db["users"]

    def is_alive(self):
        try:
            self.client.is_primary
            return True
        except errors.ServerSelectionTimeoutError:
            return False

    def get_users(self) -> list[User]:
        return list(self.users.find())

    def get_user(self, user_id: str) -> User | None:
        if self.users.find_one({"id": user_id}):
            return User(**self.users.find_one({"id": user_id}))
        return None

    def create_user(self, user: User) -> User | None:
        if self.users.find_one({"id": user.id}):
            return None
        self.users.insert_one(user.model_dump())
        return user

    def delete_user(self, user_id: str) -> bool:
        if self.users.find_one({"id": user_id}):
            self.users.delete_one({"id": user_id})
            return True
        return False

    def update_user(self, user_id: str, user: User) -> User | None:
        if self.users.find_one({"id": user_id}):
            self.users.update_one({"id": user_id}, {"$set": user.model_dump()})
            return user
        return None
