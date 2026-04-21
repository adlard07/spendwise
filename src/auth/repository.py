import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.database.dynamo.services import DatabaseServices
from src.models.users import User, UserInDB

load_dotenv(override=True)


class AuthenticationRepository:
    def __init__(self):
        self.SECRET_KEY: str = os.getenv("SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_mins = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
        self.dbs = DatabaseServices()

    # ==== helpers ====

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return plain_password == hashed_password

    # ==== user authentication ====

    def authenticate_user(self, email: str, password: str):
        user = self.dbs.get_user(email=email)
        print("User:", user)
        print("\n")
        if not user:
            return None

        stored_hash = user.get("password")
        if not stored_hash:
            return None

        if not self.verify_password(password, stored_hash):
            return None

        return user

    # ==== token ====

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

    # ==== FastAPI dependency methods ====

    async def get_current_user(self, token: str) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
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

    def generate_csrf_token(self) -> str:
        return secrets.token_urlsafe(32)

    def validate_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        if not cookie_token or not header_token:
            return False
        return secrets.compare_digest(cookie_token, header_token)
