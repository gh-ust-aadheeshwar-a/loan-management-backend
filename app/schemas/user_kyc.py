from pydantic import BaseModel, Field
from datetime import date
from app.enums.user import Gender

class AddressSchema(BaseModel):
    line1: str
    city: str
    state: str
    pincode: str


class UserKYCRequest(BaseModel):
    aadhaar: str = Field(..., min_length=12, max_length=12)
    pan: str
    dob: date
    gender: Gender
    occupation: str
    address: AddressSchema
