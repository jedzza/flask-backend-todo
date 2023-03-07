from pydantic import BaseModel, Field


class PasswordResetModel(BaseModel):
    password: str = Field(...)
