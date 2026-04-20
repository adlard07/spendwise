import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from src.models.users import User, UserInDB
from src.database.dynamo.services import DatabaseServices


load_dotenv(override=True)


class Authentication:
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_mins = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
        self.dbs = DatabaseServices

    # ---- password helpers ----

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    # ---- user authentication ----

    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user = self.dbs.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    # ---- token helpers ----

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta
            if expires_delta
            else timedelta(minutes=self.access_token_expire_mins)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    # ---- FastAPI dependency methods ----

    async def get_current_user(self, token: str) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = self.dbs.get_user(username)
        if user is None:
            raise credentials_exception
        return user

    async def get_current_active_user(self, user: User) -> User:
        if user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user


auth = Authentication()

# Re-export constants / schemes that url.py needs
oauth2_scheme = auth.oauth2_scheme
access_token_expire_mins = auth.access_token_expire_mins


def get_password_hash(password: str) -> str:
    return auth.get_password_hash(password)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    return auth.authenticate_user(username, password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return auth.create_access_token(data, expires_delta)


async def get_current_user(token: str = Depends(oauth2_scheme),) -> User:
    return await auth.get_current_user(token)


async def get_current_active_user(current_user: User = Depends(get_current_user),) -> User:
    return await auth.get_current_active_user(current_user)