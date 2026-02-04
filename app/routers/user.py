from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.services.user_service import UserService
from app.schemas.user_kyc import UserKYCRequest

router = APIRouter(prefix="/users", tags=["Users"])
service = UserService()


@router.get("/me")
async def get_my_profile(
    auth: AuthContext = Depends(get_current_user)
):
    # 🔐 Only users can view their own profile
    if auth.role != Role.USER:
        raise HTTPException(status_code=403, detail="Access denied")

    user = await service.get_user_by_id(auth.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.post("/me/kyc", status_code=200)
async def submit_kyc(
    payload: UserKYCRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.USER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        await service.submit_kyc(auth.user_id, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {"message": "KYC completed successfully"}
