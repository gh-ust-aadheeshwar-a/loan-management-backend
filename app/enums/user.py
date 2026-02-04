from enum import Enum

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class KYCStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"

class UserApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELETED = "DELETED"

