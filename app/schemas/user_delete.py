from pydantic import BaseModel
from typing import Optional
from enum import Enum

class DeleteDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"

class UserDeleteDecisionRequest(BaseModel):
    decision: DeleteDecision
    reason: Optional[str] = None
class UserDeleteRequest(BaseModel):
    reason: str
