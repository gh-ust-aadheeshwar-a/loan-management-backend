from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.schemas.loan_decision import LoanDecisionRequest
from app.services.loan_manager_service import LoanManagerService

router = APIRouter(
    prefix="/manager/loan",
    tags=["Loan Manager"]
)

service = LoanManagerService()


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
