import datetime

from pydantic import BaseModel, EmailStr


class TaskModel(BaseModel):
    description: str
    done: bool
    started: datetime.datetime

