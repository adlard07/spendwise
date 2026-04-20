from fastapi import APIRouter, HTTPException, status

from src.auth.auth import get_password_hash
from src.database.dynamo.services import DatabaseServices
from src.models.auth import SignupResponse
from src.models.users import CreateUser
from utils.logger import logging

router = APIRouter(
    prefix="/auth",
    tags=[
        "authentication",
        "user management",
        "signup operations",
    ],
)

dbs = DatabaseServices()


@router.post(
    "/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED
)
async def signup(payload: CreateUser):
    """Register a new user."""
    try:
        existing = dbs.get_user_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        payload.password = get_password_hash(payload.password)

        dbs.create_user(payload)
        logging.info(f"User created successfully: {payload.username}")
        print(payload)

        return SignupResponse(
            message="User created successfully", username=payload.username
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
