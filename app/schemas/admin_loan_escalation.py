from pydantic import BaseModel
from typing import Optional
from enum import Enum

class AdminLoanDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"

class AdminLoanDecisionRequest(BaseModel):
    decision: AdminLoanDecision
    reason: Optional[str]
