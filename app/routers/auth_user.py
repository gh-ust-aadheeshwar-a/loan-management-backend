from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth_user import UserRegisterRequest, UserRegisterResponse, UserLoginRequest, TokenResponse
from app.services.user_service import UserService
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth/user", tags=["Auth - User"])
service = UserService()


@router.post("/register", response_model=UserRegisterResponse, status_code=201)
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

@router.post("/login", response_model=TokenResponse)
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
