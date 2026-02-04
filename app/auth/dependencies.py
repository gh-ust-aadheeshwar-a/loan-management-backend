from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth.security import decode_access_token
from app.enums.role import Role
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/manager/login")


class AuthContext(BaseModel):
    user_id: str
    role: Role


async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> AuthContext:
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return AuthContext(
        user_id=payload["sub"],
        role=Role(payload["role"])
    )
