from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.auth.security import decode_access_token
from app.enums.role import Role

# =====================
# HTTP Bearer Scheme
# =====================
security = HTTPBearer()

# =====================
# Auth Context
# =====================
class AuthContext(BaseModel):
    user_id: str
    role: Role

# =====================
# Generic Resolver
# =====================
def _resolve_user(token: str, expected_roles: list[Role]) -> AuthContext:
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    role = Role(payload["role"])

    if role not in expected_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return AuthContext(
        user_id=payload["sub"],
        role=role
    )

# =====================
# ANY AUTHENTICATED USER
# =====================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthContext:
    return _resolve_user(
        credentials.credentials,
        expected_roles=[
            Role.USER,
            Role.ADMIN,
            Role.BANK_MANAGER,
            Role.LOAN_MANAGER
        ]
    )

# =====================
# ROLE-SPECIFIC
# =====================
async def get_current_admin(
    auth: AuthContext = Depends(get_current_user)
) -> AuthContext:
    if auth.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")
    return auth


async def get_current_bank_manager(
    auth: AuthContext = Depends(get_current_user)
) -> AuthContext:
    if auth.role != Role.BANK_MANAGER:
        raise HTTPException(403, "Bank Manager access required")
    return auth


async def get_current_loan_manager(
    auth: AuthContext = Depends(get_current_user)
) -> AuthContext:
    if auth.role != Role.LOAN_MANAGER:
        raise HTTPException(403, "Loan Manager access required")
    return auth
