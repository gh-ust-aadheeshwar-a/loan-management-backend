from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.manager_auth_service import ManagerAuthService

router = APIRouter(
    prefix="/auth/manager",
    tags=["Auth - Manager"]
)

service = ManagerAuthService()

@router.post(
    "/login",
    summary="Manager Login (Bank / Loan)",
    description="""
Authenticate a **Manager** using manager ID and password.

This endpoint is used by:
- **Bank Manager**
- **Loan Manager**

Returns a JWT access token containing:
- role = `BANK_MANAGER` or `LOAN_MANAGER`

Use this token in Swagger **Authorize 🔐** to access manager-protected APIs.
"""
)
async def manager_login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        token = await service.login_manager(
            manager_id=form_data.username,
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
