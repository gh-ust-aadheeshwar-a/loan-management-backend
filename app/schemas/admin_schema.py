from pydantic import BaseModel

class AdminUserDeletionRequest(BaseModel):
    reason: str

class AdminEscalatedLoanDecision(BaseModel):
    decision: str
    reason: str
