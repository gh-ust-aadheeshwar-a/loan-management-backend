from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field
from app.utils.object_id import PyObjectId
from app.enums.user import Gender, KYCStatus, UserApprovalStatus


class Address(BaseModel):
    line1: str
    city: str
    state: str
    pincode: str


class Nominee(BaseModel):
    name: Optional[str]
    relation: Optional[str]


class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")

    aadhaar: str
    pan: str
    name: str
    phone: str
    password_hash: str

    dob: date
    gender: Gender
    address: Address
    occupation: str
    nominee: Optional[Nominee]

    is_minor: bool
    kyc_status: KYCStatus
    approval_status: UserApprovalStatus

    approved_by_manager_id: Optional[PyObjectId]

    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
