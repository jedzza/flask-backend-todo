from _datetime import datetime

from pydantic import BaseModel, Field


class ResetTokenModel(BaseModel):
    passcode: str = Field(...)
    expiry: datetime = Field(...)
    used: bool = Field(False)
