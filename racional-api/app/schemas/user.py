from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email:     EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone:     str | None = Field(None, max_length=50)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone:     str | None = Field(None, max_length=50)


class UserResponse(BaseModel):
    id:         UUID
    email:      str
    full_name:  str
    phone:      str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
