from typing import List, Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupResponse(BaseModel):
    message: str
    username: str | None
    user_id: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = []


class APIKeyCreatedResponse(BaseModel):
    key_id: str
    name: str
    prefix: str
    scopes: List[str]
    created_at: str
    raw_key: str  # Shown only once at creation


class APIKeyPublic(BaseModel):
    key_id: str
    name: str
    prefix: str
    scopes: List[str]
    created_at: str
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None
    revoked: bool = False
