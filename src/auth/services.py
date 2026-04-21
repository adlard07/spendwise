from datetime import timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends

from src.auth.repository import AuthenticationRepository
from src.models.users import User, UserInDB

load_dotenv(override=True)

auth = AuthenticationRepository()

oauth2_scheme = auth.oauth2_scheme
access_token_expire_mins = auth.access_token_expire_mins


def get_password_hash(password: str) -> str:
    return auth.get_password_hash(password)


def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    return auth.authenticate_user(email, password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return auth.create_access_token(data, expires_delta)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    return await auth.get_current_user(token)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return await auth.get_current_active_user(current_user)


def generate_csrf_token() -> str:
    return auth.generate_csrf_token()


def validate_csrf_token(cookie_token: str, header_token: str) -> bool:
    return auth.validate_csrf_token(cookie_token, header_token)
