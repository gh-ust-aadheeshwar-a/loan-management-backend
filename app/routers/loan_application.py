from fastapi import APIRouter, Header, HTTPException, status, Depends
from app.schemas.loan_application import (
    LoanApplicationCreateRequest,
    LoanApplicationResponse,
    LoanApplicationDetailResponse
)
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


@router.get("/loans/{loan_id}")
async def get_loan(
    loan_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.USER:
        raise HTTPException(403)

    return await service.get_loan_application(loan_id)
