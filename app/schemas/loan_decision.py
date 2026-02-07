from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from app.enums.loan import SystemDecision

# =========================
# Manual Decision (Manager)
# =========================
class LoanDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class LoanDecisionRequest(BaseModel):
    decision: LoanDecision
    reason: Optional[str] = None


# =========================
# Auto Decision (System)
# =========================
class LoanAutoDecisionRequest(BaseModel):
    system_decision: SystemDecision


# =========================
# Finalization
# =========================
class LoanFinalizeRequest(BaseModel):
    interest_rate: float
    tenure_months: int


# =========================
# Escalation
# =========================
class LoanEscalationRequest(BaseModel):
    reason: str = Field(..., min_length=5)
