from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.schemas.user_decision import UserApprovalDecisionRequest
from app.schemas.user_delete import UserDeleteRequest
from app.services.bank_manager_service import BankManagerService
from typing import Optional
from app.schemas.user_delete import UserDeleteDecisionRequest

router = APIRouter(
    prefix="/manager/bank",
    tags=["Bank Manager"]
)

service = BankManagerService()

@router.get("/users")
async def list_users(
    approval_status: Optional[str] = Query(None),
    kyc_status: Optional[str] = Query(None),
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.BANK_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    return await service.list_users(
        approval_status=approval_status,
        kyc_status=kyc_status
    )

@router.get("/users/{user_id}/kyc")
async def review_user_kyc(
    user_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.BANK_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        return await service.get_user_kyc_details(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.post("/users/{user_id}/decision", status_code=200)
async def decide_user(
    user_id: str,
    payload: UserApprovalDecisionRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.BANK_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        await service.decide_user(
            manager_id=auth.user_id,
            user_id=user_id,
            decision=payload.decision,
            reason=payload.reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {"message": f"User {payload.decision.lower()}ed successfully"}

@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.BANK_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        return await service.get_user_details(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
# @router.post("/users/{user_id}/delete")
# async def delete_user(
#     user_id: str,
#     payload: UserDeleteRequest,
#     auth: AuthContext = Depends(get_current_user)
# ):
#     if auth.role != Role.BANK_MANAGER:
#         raise HTTPException(status_code=403, detail="Access denied")

#     try:
#         await service.delete_user(
#             manager_id=auth.user_id,
#             user_id=user_id,
#             reason=payload.reason
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/delete/decision")
async def handle_user_deletion_escalation(
    user_id: str,
    payload: UserDeleteDecisionRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.BANK_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        await service.handle_user_deletion_escalation(
            manager_id=auth.user_id,
            user_id=user_id,
            decision=payload.decision,
            reason=payload.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": f"User deletion {payload.decision.lower()}ed successfully"}


