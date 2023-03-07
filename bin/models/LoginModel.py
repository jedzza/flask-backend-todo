from pydantic import BaseModel, EmailStr, Field

from bin.models.TaskModel import TaskModel


class LoginModel(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)
