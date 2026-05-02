import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from utils.utils import generate_uuid, get_current_timestamp


class Role(str):
    ADMIN = "admin"
    USER = "user"


class Currency(str):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"


class CreateUser(BaseModel):
    user_id: str = Field(default_factory=generate_uuid)
    first_name: str
    last_name: str
    username: Optional[str] | None = None
    email: EmailStr
    password: str
    created_at: Optional[datetime.datetime] = Field(
        default_factory=get_current_timestamp
    )
    updated_at: Optional[datetime.datetime] = Field(
        default_factory=get_current_timestamp
    )
    role: str = Role.USER
    currency: str = Currency.INR
    disabled: bool = False

    @model_validator(mode="after")
    def set_username(self):
        if not self.username:
            self.username = f"{self.first_name.lower()}_{self.last_name.lower()}"
        return self


class User(BaseModel):
    user_id: str
    username: str
    email: str
    role: str = Role.USER
    disabled: bool = False


class UserInDB(User):
    hashed_password: str
