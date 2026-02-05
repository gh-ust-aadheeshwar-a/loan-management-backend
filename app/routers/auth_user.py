from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth_user import (
    UserRegisterRequest,
    UserRegisterResponse,
    TokenResponse
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/auth/user",
    tags=["Auth - User"]
)

service = UserService()

# =========================
# USER REGISTRATION
# =========================
@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=201,
    summary="User Registration",
    description="""
Register a **new user** using phone number and password.

- Creates a user in `PENDING` approval state
- KYC must be completed after registration
- Bank Manager approval is required before loan access
"""
)
async def register_user(payload: UserRegisterRequest):
    try:
        user_id = await service.register_user(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return UserRegisterResponse(
        user_id=user_id,
        message="Registration successful. Please complete KYC."
    )

# =========================
# USER LOGIN
# =========================
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="""
Authenticate an **end user** using phone number and password.

Returns a JWT access token containing:
- role = `USER`

Use this token in Swagger **Authorize 🔐** to access user-protected APIs.
"""
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        token = await service.login_user(
            phone=form_data.username,
            password=form_data.password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    return TokenResponse(access_token=token)
