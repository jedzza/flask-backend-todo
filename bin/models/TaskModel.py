from pydantic import BaseModel, EmailStr

class TaskModel(BaseModel):
    description: str
