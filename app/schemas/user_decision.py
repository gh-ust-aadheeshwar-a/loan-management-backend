from pydantic import BaseModel
from typing import Optional
from enum import Enum

class UserDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"

class UserApprovalDecisionRequest(BaseModel):
    decision: UserDecision
    reason: Optional[str]
