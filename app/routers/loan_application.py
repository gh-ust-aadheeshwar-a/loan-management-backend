from fastapi import APIRouter, Header, HTTPException, status, Depends

from app.schemas.loan_application import (
    LoanApplicationCreateRequest,
    LoanApplicationResponse,
    LoanApplicationDetailResponse
)
from app.schemas.loan_decision_query import LoanDecisionResponse
from app.services.loan_application_service import LoanApplicationService
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role

router = APIRouter(prefix="/loans", tags=["Loans"])
service = LoanApplicationService()


@router.post("", response_model=LoanApplicationResponse, status_code=201)
async def apply_loan(
    payload: LoanApplicationCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.USER:
        raise HTTPException(status_code=403)

    try:
        loan_id, reused = await service.create_loan_application(
            user_id=auth.user_id,
            payload=payload,
            idempotency_key=idempotency_key
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if reused:
        return LoanApplicationResponse(
            loan_id=loan_id,
            status="EXISTING",
            message="Loan application already exists"
        )

    return LoanApplicationResponse(
        loan_id=loan_id,
        status="CREATED",
        message="Loan application submitted successfully"
    )


@router.get("/{loan_id}")
async def get_loan(
    loan_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.USER:
        raise HTTPException(status_code=403)

    return await service.get_loan_application(loan_id)


@router.get(
    "/{loan_id}/decision",
    response_model=LoanDecisionResponse,
    summary="Get loan decision details"
)
async def get_loan_decision(
    loan_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role == Role.BANK_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        decision = await service.get_loan_decision(loan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 🔐 OWNERSHIP CHECK (CRITICAL)
    if auth.role == Role.USER and decision["user_id"] != auth.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Remove internal field before response
    decision.pop("user_id")

    return decision
