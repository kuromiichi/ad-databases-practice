from datetime import datetime
from uuid import UUID, uuid4

from mariadb import connect

from src.models.task import Task, TaskCreate
from src.models.user import User, UserLogin


root_token = "root"


class MariaDBService:
    def __init__(self, user, passwd, db):
        self.conn = connect(
            user=user,
            password=passwd,
            host="mariadb",
            port=3306,
            database=db,
            autocommit=True,
        )
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(255) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL,
                    uuid VARCHAR(36) NOT NULL
                );     
            """
        )

        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    text VARCHAR(500) NOT NULL,
                    created_at VARCHAR(255) NOT NULL,
                    updated_at VARCHAR(255) NOT NULL,
                    is_checked BOOLEAN NOT NULL,
                    is_important BOOLEAN NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
                );
            """
        )

    def is_alive(self) -> dict:
        try:
            self.cursor.execute("SELECT 1")
            return {"is_alive": True, "db": "mariadb"}
        except Exception:
            return {"is_alive": False, "db": "mariadb"}

    def get_users(self, token: str) -> list[User] | str:
        if token != root_token:
            return "Unauthorized"
        self.cursor.execute("SELECT * FROM users")
        users = self.cursor.fetchall()
        users_with_tasks = []
        for user in users:
            user = User(id=user[0], password=user[1], uuid=UUID(user[2]))
            self.cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (user.id,))
            tasks = self.cursor.fetchall()
            user.tasks = [
                Task(
                    id=UUID(task[0]),
                    user_id=task[1],
                    text=task[2],
                    created_at=task[3],
                    updated_at=task[4],
                    is_checked=task[5],
                    is_important=task[6],
                )
                for task in tasks
            ]
            users_with_tasks.append(user)
        return users_with_tasks

    def get_user(self, user_id: str, token: str) -> User | str:
        if token != root_token:
            return "Unauthorized"
        self.cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = self.cursor.fetchone()
        if user:
            user = User(id=user[0], password=user[1], uuid=UUID(user[2]))
            self.cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (user.id,))
            tasks = self.cursor.fetchall()
            user.tasks = [Task(*task) for task in tasks]
            return user
        return "User not found"

    def get_token(self, user: UserLogin) -> str | None:
        self.cursor.execute(
            "SELECT uuid FROM users WHERE id = %s AND password = %s",
            (user.id, user.password),
        )
        match = self.cursor.fetchone()
        if match:
            return match[0]
        return None

    def create_user(self, user: UserLogin) -> User | str:
        self.cursor.execute("SELECT * FROM users WHERE id = %s", (user.id,))
        if self.cursor.fetchone():
            return "Email already registered"
        new_user = User(**user.model_dump(), uuid=uuid4())
        self.cursor.execute(
            "INSERT INTO users (id, password, uuid) VALUES (%s, %s, %s)",
            (new_user.id, new_user.password, str(new_user.uuid)),
        )
        return new_user

    def delete_user(self, user_id: str, token: str) -> bool | str:
        if token != root_token:
            return "Unauthorized"
        self.cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        if self.cursor.fetchone():
            self.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return True
        return "User not found"

    def update_user(self, user_id: str, token: str, user: UserLogin) -> UserLogin | str:
        self.cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        existing_user = self.cursor.fetchone()
        if existing_user:
            if token != root_token and token != existing_user[2]:
                return "Unauthorized"
            self.cursor.execute(
                "UPDATE users SET id = %s, password = %s WHERE id = %s",
                (user.id, user.password, user_id),
            )
            return user
        return "User not found"

    def get_tasks(self, token: str) -> list[Task] | str:
        if token == root_token:
            self.cursor.execute("SELECT * FROM tasks")
            tasks = self.cursor.fetchall()
            return [
                Task(
                    id=UUID(task[0]),
                    user_id=task[1],
                    text=task[2],
                    created_at=task[3],
                    updated_at=task[4],
                    is_checked=task[5],
                    is_important=task[6],
                )
                for task in tasks
            ]
        self.cursor.execute("SELECT * FROM users WHERE uuid = %s", (token,))
        user = self.cursor.fetchone()
        if user:
            self.cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (user[0],))
            tasks = self.cursor.fetchall()
            return [
                Task(
                    id=UUID(task[0]),
                    user_id=task[1],
                    text=task[2],
                    created_at=task[3],
                    updated_at=task[4],
                    is_checked=task[5],
                    is_important=task[6],
                )
                for task in tasks
            ]
        return "Invalid token"

    def get_task(self, task_id: UUID, token: str) -> Task | str:
        self.cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = self.cursor.fetchone()
        if task:
            self.cursor.execute("SELECT * FROM users WHERE id = %s", (task[1],))
            user = self.cursor.fetchone()
            if user or token == root_token:
                if token == root_token or token == user[2]:
                    return Task(
                        id=UUID(task[0]),
                        user_id=task[1],
                        text=task[2],
                        created_at=task[3],
                        updated_at=task[4],
                        is_checked=task[5],
                        is_important=task[6],
                    )
            return "Unauthorized"
        return "Task not found"

    def create_task(self, task: TaskCreate, token: str) -> Task | str:
        self.cursor.execute("SELECT * FROM users WHERE uuid = %s", (token,))
        user = self.cursor.fetchone()
        if user:
            new_task = Task(
                **task.model_dump(),
                id=uuid4(),
                user_id=user[0],
                created_at=str(datetime.now()),
                updated_at=str(datetime.now()),
            )
            self.cursor.execute(
                "INSERT INTO tasks (id, user_id, text, created_at, updated_at, is_checked, is_important) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    str(new_task.id),
                    new_task.user_id,
                    new_task.text,
                    new_task.created_at,
                    new_task.updated_at,
                    new_task.is_checked,
                    new_task.is_important,
                ),
            )
            return new_task
        return "Invalid token"

    def delete_task(self, task_id: UUID, token: str) -> bool | str:
        self.cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = self.cursor.fetchone()
        if task:
            self.cursor.execute("SELECT * FROM users WHERE id = %s", (task[1],))
            user = self.cursor.fetchone()
            if user or token == root_token:
                if token == root_token or token == user[2]:
                    self.cursor.execute("DELETE FROM tasks WHERE id = %s", (str(task_id),))
                    return True
            return "Unauthorized"
        return "Task not found"

    def update_task(self, task_id: UUID, token: str, task: TaskCreate) -> Task | str:
        self.cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        existing_task = self.cursor.fetchone()
        if existing_task:
            self.cursor.execute("SELECT * FROM users WHERE id = %s", (existing_task[1],))
            user = self.cursor.fetchone()
            if user or token == root_token:
                if token == root_token or token == user[2]:
                    self.cursor.execute(
                        "UPDATE tasks SET text = %s, updated_at = %s, is_checked = %s, is_important = %s WHERE id = %s",
                        (
                            task.text,
                            str(datetime.now()),
                            task.is_checked,
                            task.is_important,
                            str(task_id),
                        ),
                    )
                    self.cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
                    updated_task = self.cursor.fetchone()
                    return Task(
                        id=UUID(updated_task[0]),
                        user_id=updated_task[1],
                        text=updated_task[2],
                        created_at=updated_task[3],
                        updated_at=updated_task[4],
                        is_checked=updated_task[5],
                        is_important=updated_task[6],
                    )
            return "Unauthorized"
        return "Task not found"

    def delete_data(self, token: str) -> bool:
        if token != root_token:
            return False
        self.cursor.execute("DELETE FROM tasks")
        self.cursor.execute("DELETE FROM users")
        return True
        
