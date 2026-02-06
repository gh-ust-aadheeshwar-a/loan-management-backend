from pydantic import BaseModel
from enum import Enum
from typing import Optional

class LoanDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"

class LoanDecisionRequest(BaseModel):
    decision: LoanDecision
    reason: Optional[str] = None

class LoanFinalizeRequest(BaseModel):
    interest_rate: float
    tenure_months: int 