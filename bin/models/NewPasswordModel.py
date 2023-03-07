from pydantic import BaseModel, Field


class NewPasswordModel(BaseModel):
    password: str = Field(...)
