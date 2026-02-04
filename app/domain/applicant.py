from pydantic import BaseModel
from datetime import date
from app.enums.user import Gender

class ApplicantDetails(BaseModel):
    full_name: str
    dob: date
    gender: Gender
    occupation: str

    class Config:
        frozen = True
