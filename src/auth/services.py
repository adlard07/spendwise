from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.repository import AuthenticationRepository

auth = AuthenticationRepository()

oauth2_scheme = auth.oauth2_scheme
access_token_expire_mins = auth.access_token_expire_mins
refresh_token_expire_days = auth.refresh_token_expire_days

_bearer = HTTPBearer(auto_error=False)


# =========================================================================
# Password
# =========================================================================


def get_password_hash(password: str) -> str:
    return auth.get_password_hash(password)


# =========================================================================
# Auth flows
# =========================================================================


def login(
    email: str,
    password: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[str, str]:
    return auth.login(email, password, user_agent=user_agent, ip_address=ip_address)


def rotate_refresh_token(
    raw_token: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[str, str]:
    return auth.rotate_refresh_token(
        raw_token, user_agent=user_agent, ip_address=ip_address
    )


def logout(raw_token: str) -> None:
    auth.logout(raw_token)


def logout_all(user_id: str) -> None:
    auth.logout_all(user_id)


# =========================================================================
# FastAPI dependencies — JWT user auth
# =========================================================================


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    return await auth.get_current_user(token)


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    return current_user


# =========================================================================
# FastAPI dependency — API key auth
# Used on MCP integration routes only (separate from JWT auth)
# =========================================================================


async def get_user_by_api_key(
    x_api_key: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
        )
    record = auth.authenticate_api_key(x_api_key)
    user = auth.dbs.get_user_by_id(record["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


# =========================================================================
# CSRF
# =========================================================================


def generate_csrf_token() -> str:
    return auth.generate_csrf_token()


def validate_csrf_token(
    cookie_token: Optional[str], header_token: Optional[str]
) -> bool:
    return auth.validate_csrf_token(cookie_token, header_token)


# =========================================================================
# API Keys
# =========================================================================


def create_api_key(
    user_id: str, name: str, scopes: List[str]
) -> Tuple[str, Dict[str, Any]]:
    return auth.create_api_key(user_id=user_id, name=name, scopes=scopes)


def revoke_api_key(key_id: str, requesting_user_id: str) -> None:
    auth.revoke_api_key(key_id, requesting_user_id)


def list_api_keys(user_id: str) -> List[Dict[str, Any]]:
    return auth.list_api_keys(user_id)
