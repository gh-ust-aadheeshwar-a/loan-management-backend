from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.schemas.loan_decision import LoanDecisionRequest
from app.services.loan_manager_service import LoanManagerService
from app.enums.loan import SystemDecision

router = APIRouter(
    prefix="/manager/loan",
    tags=["Loan Manager"]
)

service = LoanManagerService()

@router.get("/applications")
async def view_loans(
    system_decision: SystemDecision | None = None,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(403)

    return await service.list_loans(system_decision)

@router.post("/applications/{loan_id}/decision")
async def decide_loan(
    loan_id: str,
    payload: LoanDecisionRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        await service.decide_loan(
            loan_id=loan_id,
            manager_id=auth.user_id,
            decision=payload.decision,
            reason=payload.reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {"message": f"Loan {payload.decision.lower()}ed successfully"}

@router.post("/applications/{loan_id}/confirm-auto")
async def confirm_auto(
    loan_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(403)

    await service.confirm_auto_approved(loan_id, auth.user_id)
    return {"message": "Auto-approved loan confirmed"}

@router.post("/applications/{loan_id}/confirm-reject")
async def confirm_reject(
    loan_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(403)

    await service.confirm_auto_rejected(loan_id, auth.user_id)
    return {"message": "Loan auto-rejected"}

@router.post("/applications/{loan_id}/escalate")
async def escalate_loan(
    loan_id: str,
    payload: dict,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    await service.escalate_to_admin(
        loan_id=loan_id,
        reason=payload["reason"],
        manager_id=auth.user_id
    )

    return {"message": "Loan escalated to admin"}
