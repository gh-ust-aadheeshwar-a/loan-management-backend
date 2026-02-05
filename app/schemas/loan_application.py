from pydantic import BaseModel, Field, HttpUrl
from app.enums.loan import LoanType,LoanApplicationStatus,SystemDecision
from typing import Optional
class LoanApplicationCreateRequest(BaseModel):
    loan_type: LoanType
    loan_amount: float
    tenure_months: int
    reason: str
    income_slip_url: HttpUrl

    monthly_income: float
    occupation: str
    pending_emis: int = 0
    previous_loans: int = 0
class LoanApplicationResponse(BaseModel):
    loan_id: str
    status: str
    message: str

class LoanApplicationDetailResponse(BaseModel):
    loan_id: str
    user_id: str

    loan_type: LoanType
    loan_amount: str
    tenure_months: int

    reason: str
    income_slip_url: str

    cibil_score: Optional[int]
    risk_category: Optional[str]
    system_decision: Optional[SystemDecision]

    status: LoanApplicationStatus
    applied_at: str