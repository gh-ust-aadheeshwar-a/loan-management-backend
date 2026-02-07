from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.utils.object_id import PyObjectId
from app.enums.transaction import TransactionType, TransactionStatus

class LoanTransaction(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    transaction_id: str
    loan_id: PyObjectId
    user_id: PyObjectId
    emi_number: Optional[int]
    amount: float
    transaction_type: TransactionType
    status: TransactionStatus
    balance_after: float
    created_at: datetime
