from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional
from app.utils.object_id import PyObjectId

class LoanRepayment(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    loan_id: PyObjectId
    user_id: PyObjectId
    emi_number: int
    due_date: date
    emi_amount: float
    status: str  # PENDING / PAID / FAILED
    attempts: int = 0
    paid_at: Optional[datetime]
