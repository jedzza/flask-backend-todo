from pydantic import BaseModel, EmailStr, Field


class ResetModel(BaseModel):
    email: EmailStr = Field(...)
    code: str = Field(...)
