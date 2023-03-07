from pydantic import BaseModel, EmailStr, Field


class ForgotModel(BaseModel):
    email: EmailStr = Field(...)
