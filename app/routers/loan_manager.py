from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.schemas.loan_decision import LoanDecisionRequest,LoanFinalizeRequest,LoanEscalationRequest
from app.services.loan_manager_service import LoanManagerService
from app.enums.loan import SystemDecision
from app.schemas.loan_decision import LoanAutoDecisionRequest

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

@router.post("/applications/{loan_id}/auto-decision")
async def auto_decision(
    loan_id: str,
    payload: LoanAutoDecisionRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    if payload.system_decision == SystemDecision.AUTO_APPROVED:
        await service.confirm_auto_approved(loan_id, auth.user_id)
        return {"message": "Loan auto-approved successfully"}

    elif payload.system_decision == SystemDecision.AUTO_REJECTED:
        await service.confirm_auto_rejected(loan_id, auth.user_id)
        return {"message": "Loan auto-rejected successfully"}

    raise HTTPException(
        status_code=400,
        detail="Invalid system decision"
    )


@router.post("/applications/{loan_id}/escalate")
async def escalate_loan(
    loan_id: str,
    payload: LoanEscalationRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    await service.escalate_to_admin(
        loan_id=loan_id,
        reason=payload.reason,
        manager_id=auth.user_id
    )

    return {"message": "Loan escalated to admin"}



@router.get("/applications/escalated")
async def get_escalated_loans(
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    return await service.list_escalated_loans()

@router.post("/applications/{loan_id}/finalize")
async def finalize_loan(
    loan_id: str,
    payload: LoanFinalizeRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        await service.finalize_loan(
            loan_id=loan_id,
            manager_id=auth.user_id,
            interest_rate=payload.interest_rate,
            tenure_months=payload.tenure_months
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Loan finalized successfully"}

@router.get("/loan/applications/finalizable")
async def get_finalizable_loans(
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    return await service.list_loans_ready_for_finalization()

# @router.get("/applications/finalizable")
# async def get_finalizable_loans(
#     auth: AuthContext = Depends(get_current_user)
# ):
#     if auth.role != Role.LOAN_MANAGER:
#         raise HTTPException(403)

#     return await service.list_loans_ready_for_finalization()
