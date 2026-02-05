from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.admin_auth_service import AdminAuthService

router = APIRouter(
    prefix="/auth/admin",
    tags=["Auth - Admin"]
)

service = AdminAuthService()

@router.post(
    "/login",
    summary="Admin Login",
    description="""
Authenticate an **Admin** using username and password.

- Returns a JWT access token
- Token contains role = `ADMIN`
- Use this token in Swagger **Authorize 🔐**

Example:
- username: `bankadmin`
- password: `admin123`
"""
)
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        token = await service.login_admin(
            username=form_data.username,
            password=form_data.password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
