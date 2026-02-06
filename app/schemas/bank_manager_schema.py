from pydantic import BaseModel, Field
from typing import Optional
from app.enums.role import Role


# =========================
# CREATE MANAGER
# =========================
class ManagerCreateRequest(BaseModel):
    manager_id: str = Field(..., description="Unique manager login ID")
    name: str
    phone: str
    password: str
    role: Role  # BANK_MANAGER or LOAN_MANAGER


# =========================
# UPDATE MANAGER
# =========================
class ManagerUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[Role] = None

