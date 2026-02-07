from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.services.account_services import AccountService

router = APIRouter(prefix="/account", tags=["Account"])
service = AccountService()

@router.post("/deposit")
async def deposit(payload: dict, auth: AuthContext = Depends(get_current_user)):
    if auth.role != Role.USER:
        raise HTTPException(403)
    await service.deposit(auth.user_id, payload["amount"])
    return {"message": "Amount added successfully"}
