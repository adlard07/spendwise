import os
from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)

from src.auth.services import (
    create_api_key,
    generate_csrf_token,
    get_current_active_user,
    get_password_hash,
    list_api_keys,
    login,
    logout,
    logout_all,
    revoke_api_key,
    rotate_refresh_token,
    validate_csrf_token,
)
from src.database.dynamo.services import DatabaseServices
from src.models.auth import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyPublic,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupResponse,
    Token,
)
from src.models.users import CreateUser, User

router = APIRouter(tags=["authentication"], prefix="/auth")
dbs = DatabaseServices()


# =========================================================================
# CSRF
# =========================================================================


@router.get("/csrf-token")
def get_csrf_token(response: Response):
    token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        samesite="strict",
        secure=os.getenv("ENV") == "production",
    )
    return {"csrf_token": token}


def _check_csrf(
    csrf_token: str = Cookie(default=None),
    x_csrf_token: str = Header(default=None),
) -> None:
    if not validate_csrf_token(csrf_token, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token invalid or missing",
        )


# =========================================================================
# Signup
# =========================================================================


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_check_csrf)],
)
async def signup(payload: CreateUser):
    existing = dbs.get_user_by_email(str(payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    payload.password = get_password_hash(payload.password)
    dbs.create_user(payload)
    return SignupResponse(
        message="User created successfully",
        username=payload.username,
        user_id=payload.user_id,
    )


# =========================================================================
# Login
# =========================================================================


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(_check_csrf)],
)
async def login_route(payload: LoginRequest, request: Request):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    access_token, refresh_token = login(
        email=payload.email,
        password=payload.password,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


# =========================================================================
# Refresh
# =========================================================================


@router.post("/refresh", response_model=Token)
async def refresh_route(payload: RefreshRequest, request: Request):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    access_token, new_refresh_token = rotate_refresh_token(
        raw_token=payload.refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return Token(access_token=access_token, refresh_token=new_refresh_token)


# =========================================================================
# Logout
# =========================================================================


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_route(payload: LogoutRequest):
    logout(payload.refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_route(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    logout_all(current_user["user_id"])


# =========================================================================
# Current user
# =========================================================================


@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    return User(
        user_id=current_user["user_id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user.get("role", "user"),
        disabled=current_user.get("disabled", False),
    )


# =========================================================================
# API Keys  (MCP server integration)
# JWT auth required to manage keys; keys are used separately with X-API-Key
# =========================================================================


@router.post(
    "/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key_route(
    payload: APIKeyCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    raw_key, record = create_api_key(
        user_id=current_user["user_id"],
        name=payload.name,
        scopes=payload.scopes,
    )
    return APIKeyCreatedResponse(
        key_id=record["key_id"],
        name=record["name"],
        prefix=record["prefix"],
        scopes=record["scopes"],
        created_at=record["created_at"],
        raw_key=raw_key,
    )


@router.get("/api-keys", response_model=List[APIKeyPublic])
async def list_api_keys_route(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    records = list_api_keys(current_user["user_id"])
    return [
        APIKeyPublic(
            key_id=r["key_id"],
            name=r["name"],
            prefix=r["prefix"],
            scopes=r.get("scopes", []),
            created_at=r["created_at"],
            last_used_at=r.get("last_used_at"),
            revoked_at=r.get("revoked_at"),
            revoked=r.get("revoked", False),
        )
        for r in records
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key_route(
    key_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    revoke_api_key(key_id=key_id, requesting_user_id=current_user["user_id"])
