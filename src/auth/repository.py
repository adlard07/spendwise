import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from src.database.dynamo.services import DatabaseServices

load_dotenv(override=True)


class AuthenticationRepository:
    def __init__(self):
        self._secret_key = str(os.getenv("SECRET_KEY"))
        self._algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_mins = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
        )
        self.refresh_token_expire_days = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")
        )
        self._pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
        self.dbs = DatabaseServices()

        if not self._secret_key:
            raise RuntimeError("SECRET_KEY environment variable is not set.")

    # =========================================================================
    # Password hashing  (Argon2 via passlib)
    # =========================================================================

    def get_password_hash(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        try:
            return self._pwd_context.verify(plain, hashed)
        except Exception:
            return False

    # =========================================================================
    # Token hashing  (SHA-256, deterministic — used for lookup)
    # =========================================================================

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    # =========================================================================
    # JWT (access tokens only)
    # Claims: sub, email, jti, type, iat, exp
    # =========================================================================

    def create_access_token(self, user_id: str, email: str, jti: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "jti": jti,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_mins),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload

    # =========================================================================
    # Refresh tokens  (opaque, stored SHA-256 hashed in DynamoDB)
    # =========================================================================

    def _issue_token_pair(
        self,
        user_id: str,
        email: str,
        user_agent: Optional[str],
        ip_address: Optional[str],
    ) -> Tuple[str, str]:
        """Returns (access_token, refresh_token)."""
        jti = str(uuid.uuid4())
        access_token = self.create_access_token(user_id=user_id, email=email, jti=jti)
        refresh_token = self._create_session(
            user_id=user_id,
            jti=jti,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return access_token, refresh_token

    def _create_session(
        self,
        user_id: str,
        jti: str,
        user_agent: Optional[str],
        ip_address: Optional[str],
    ) -> str:
        """Persists a new session; returns the raw (unhashed) refresh token."""
        raw_token = secrets.token_urlsafe(64)
        token_hash = self._hash_token(raw_token)
        expires_at = int(
            (
                datetime.now(timezone.utc)
                + timedelta(days=self.refresh_token_expire_days)
            ).timestamp()
        )
        session = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_id,
            "token_hash": token_hash,
            "jti": jti,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "revoked": False,
            "revoked_at": None,
            "user_agent": user_agent,
            "ip_address": ip_address,
        }
        self.dbs.create_session(session)
        return raw_token

    # =========================================================================
    # Auth flows
    # =========================================================================

    def login(
        self,
        email: str,
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, str]:
        user = self.dbs.get_user_by_email(email)
        print(user)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        stored_password = user.get("password", "")

        password_valid = False

        try:
            password_valid = (
                self.verify_password(password, stored_password)
                or password == stored_password
            )
        except Exception:
            password_valid = False

        # Case 2: DB password is plain text, only for old/testing users
        # if not password_valid and password == stored_password:
        #     password_valid = True

        #     # Optional but recommended: migrate plain password to hash
        #     hashed_password = self.get_password_hash(password)
        #     self.dbs.update_user(user["user_id"], updates={"password": hashed_password})

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.get("disabled"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        return self._issue_token_pair(
            user_id=user["user_id"],
            email=user["email"],
            user_agent=user_agent,
            ip_address=ip_address,
        )

    def rotate_refresh_token(
        self,
        raw_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Validates old refresh token, revokes it, issues a new token pair.
        Detects reuse: if the token was already revoked, all sessions for that
        user are immediately revoked (refresh token rotation + reuse detection).
        Returns (access_token, refresh_token).
        """
        token_hash = self._hash_token(raw_token)
        session = self.dbs.get_session_by_token_hash(token_hash)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if session.get("revoked"):
            # Reuse detected — invalidate all active sessions for this user.
            self.dbs.revoke_all_user_sessions(session["user_id"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token already used. All sessions have been revoked.",
            )

        now_ts = int(datetime.now(timezone.utc).timestamp())
        if int(session.get("expires_at", 0)) < now_ts:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        # Revoke the consumed token before issuing a new pair.
        self.dbs.revoke_session(session["session_id"])

        user = self.dbs.get_user_by_id(session["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if user.get("disabled"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        return self._issue_token_pair(
            user_id=user["user_id"],
            email=user["email"],
            user_agent=user_agent,
            ip_address=ip_address,
        )

    def logout(self, raw_token: str) -> None:
        """Revokes a single session."""
        token_hash = self._hash_token(raw_token)
        session = self.dbs.get_session_by_token_hash(token_hash)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        self.dbs.revoke_session(session["session_id"])

    def logout_all(self, user_id: str) -> None:
        """Revokes all active sessions for a user."""
        self.dbs.revoke_all_user_sessions(user_id)

    # =========================================================================
    # Current user (FastAPI dependency)
    # =========================================================================

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        payload = self.decode_access_token(token)
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
            )
        user = self.dbs.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        if user.get("disabled"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        return user

    # =========================================================================
    # CSRF
    # =========================================================================

    def generate_csrf_token(self) -> str:
        return secrets.token_urlsafe(32)

    def validate_csrf_token(
        self, cookie_token: Optional[str], header_token: Optional[str]
    ) -> bool:
        if not cookie_token or not header_token:
            return False
        return secrets.compare_digest(cookie_token, header_token)

    # =========================================================================
    # API Keys
    # Format: mcp_{8-char-prefix}_{url-safe-secret}
    # Prefix is derived from key_id for guaranteed uniqueness.
    # Only SHA-256 hash is stored — raw key shown once at creation.
    # =========================================================================

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: List[str],
    ) -> Tuple[str, Dict[str, Any]]:
        """Returns (raw_key, record). raw_key must be shown to the user exactly once."""
        key_id = str(uuid.uuid4())
        prefix = key_id.replace("-", "")[:8]
        raw_secret = secrets.token_urlsafe(40)
        raw_key = f"mcp_{prefix}_{raw_secret}"
        key_hash = self._hash_token(raw_key)

        record: Dict[str, Any] = {
            "key_id": key_id,
            "user_id": user_id,
            "name": name,
            "prefix": prefix,
            "key_hash": key_hash,
            "scopes": scopes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used_at": None,
            "revoked_at": None,
            "revoked": False,
        }
        self.dbs.create_api_key(record)
        return raw_key, record

    def authenticate_api_key(self, raw_key: str) -> Dict[str, Any]:
        """Validates an API key and returns its record. Raises 401 on failure."""
        if not raw_key.startswith("mcp_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
            )
        parts = raw_key.split("_", 2)
        if len(parts) != 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
            )
        prefix = parts[1]
        record = self.dbs.get_api_key_by_prefix(prefix)

        if not record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        if record.get("revoked"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
            )

        expected_hash = self._hash_token(raw_key)
        if not secrets.compare_digest(record["key_hash"], expected_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        self.dbs.update_api_key_last_used(record["key_id"])
        return record

    def revoke_api_key(self, key_id: str, requesting_user_id: str) -> None:
        record = self.dbs.get_api_key(key_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )
        if record["user_id"] != requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
            )
        if record.get("revoked"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="API key already revoked"
            )
        self.dbs.revoke_api_key(key_id)

    def list_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        return self.dbs.list_api_keys_by_user(user_id)
