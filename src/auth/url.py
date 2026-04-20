from fastapi import APIRouter, Depends

from auth.auth import get_current_active_user
from auth.login import router as login_router
from auth.signup import router as signup_router
from src.models.users import User

router = APIRouter()

# Mount sub-routers (login + signup already carry /auth prefix)
router.include_router(login_router)
router.include_router(signup_router)


# ---- additional auth-scoped endpoints ----


@router.get("/auth/users/me", response_model=User, tags=["authentication"])
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    """Return the currently authenticated user."""
    return current_user
