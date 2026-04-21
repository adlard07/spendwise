import os
from datetime import timedelta

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.services import (
    access_token_expire_mins,
    authenticate_user,
    create_access_token,
    generate_csrf_token,
    get_current_active_user,
    get_password_hash,
    validate_csrf_token,
)
from src.database.dynamo.services import DatabaseServices
from src.models.auth import LoginRequest, SignupResponse, Token
from src.models.users import CreateUser, User
from utils.logger import logging

router = APIRouter(tags=["authentication"], prefix="/auth")
dbs = DatabaseServices()


@router.get("/csrf-token")
def get_csrf_token(response: Response):
    try:
        token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token",
            value=token,
            httponly=False,
            samesite="strict",
            secure=os.getenv("ENV") == "production",
        )
        return {"csrf_token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _check_csrf(
    csrf_token: str = Cookie(default=None),
    x_csrf_token: str = Header(default=None),
):
    try:
        if not validate_csrf_token(csrf_token, x_csrf_token):
            raise HTTPException(status_code=403, detail="CSRF token invalid or missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    try:
        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=Token, dependencies=[Depends(_check_csrf)])
async def login(payload: LoginRequest):
    try:
        print("Payload:", payload)
        print("\n")
        user = authenticate_user(payload.email, payload.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={"sub": user.get("email")},
            expires_delta=timedelta(minutes=access_token_expire_mins),
        )
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=201,
    dependencies=[Depends(_check_csrf)],
)
async def signup(payload: CreateUser):
    try:
        existing = dbs.get_user_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        payload.password = get_password_hash(payload.password)
        dbs.create_user(payload)
        logging.info(f"User created: {payload.username}")
        return SignupResponse(
            message="User created successfully", username=payload.username
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
