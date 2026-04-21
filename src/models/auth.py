from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    message: str
    username: str
