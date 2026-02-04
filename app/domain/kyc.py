from pydantic import BaseModel
from app.enums.user import KYCStatus, UserApprovalStatus

class KYCInfo(BaseModel):
    aadhaar_masked: str
    pan: str
    kyc_status: KYCStatus
    approval_status: UserApprovalStatus
    is_minor: bool

    class Config:
        frozen = True
