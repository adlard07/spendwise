from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.models.auth import Token
from auth.auth import (
    authenticate_user,
    create_access_token,
    access_token_expire_mins,
)

router = APIRouter(tags=["authentication"], prefix="/auth")


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return a JWT access token.
    Accepts application/x-www-form-urlencoded with `username` and `password`.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=access_token_expire_mins),
    )
    return Token(access_token=access_token, token_type="bearer")