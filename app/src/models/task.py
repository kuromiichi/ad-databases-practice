from pydantic import BaseModel
from uuid import UUID


class Task(BaseModel):
    id: UUID
    user_id: str
    text: str
    created_at: str
    updated_at: str
    is_checked: bool
    is_important: bool
