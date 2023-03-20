import datetime

from pydantic import BaseModel, EmailStr


class TaskModel(BaseModel):
    description: str
    complete: bool
    started: str

