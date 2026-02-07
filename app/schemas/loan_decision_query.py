from pydantic import BaseModel
from typing import Optional
from app.enums.loan import SystemDecision, LoanApplicationStatus


class LoanDecisionResponse(BaseModel):
    loan_id: str
    system_decision: SystemDecision
    final_status: LoanApplicationStatus
    decision_reason: Optional[str] = None
    decided_at: Optional[str] = None
