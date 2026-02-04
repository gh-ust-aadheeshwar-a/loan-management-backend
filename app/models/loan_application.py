from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import Decimal128
from app.utils.object_id import PyObjectId
from app.enums.loan import LoanType, LoanApplicationStatus, SystemDecision


class LoanApplication(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")

    user_id: PyObjectId
    loan_type: LoanType
    loan_amount: Decimal128
    tenure_months: int

    reason: str
    income_slip_url: str

    cibil_score: Optional[int]
    risk_category: Optional[str]
    system_decision: Optional[SystemDecision]

    status: LoanApplicationStatus
    applied_at: datetime

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
