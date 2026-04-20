from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class SignupResponse(BaseModel):
    message: str
    username: str
    