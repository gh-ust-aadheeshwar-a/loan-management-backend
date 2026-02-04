from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import Decimal128
from app.utils.object_id import PyObjectId


class Loan(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")

    loan_application_id: PyObjectId
    user_id: PyObjectId

    approved_by: PyObjectId
    approved_role: str

    principal_amount: Decimal128
    interest_rate: Decimal128
    tenure_months: int
    emi_amount: Decimal128

    loan_status: str
    disbursed_at: Optional[datetime]
    closed_at: Optional[datetime]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
