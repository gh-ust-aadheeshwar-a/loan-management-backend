from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.services.admin_service import AdminService
from app.schemas.admin_manager import CreateManagerRequest

router = APIRouter(prefix="/admin", tags=["Admin"])
service = AdminService()

# ========================
# ADMIN SELF
# ========================
@router.get("/me")
async def admin_me(auth: AuthContext = Depends(get_current_user)):
    if auth.role != Role.ADMIN:
        raise HTTPException(403, "Admin access required")

    return {"admin_id": auth.user_id, "role": "ADMIN"}

# ========================
# MANAGER MANAGEMENT
# ========================
@router.get("/managers")
async def list_managers(auth: AuthContext = Depends(get_current_user)):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    return await service.list_managers()

@router.post("/managers")
async def create_manager(
    payload: CreateManagerRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    await service.create_manager(payload)
    return {"message": "Manager created"}

@router.put("/managers/{manager_id}")
async def update_manager(
    manager_id: str,
    payload: dict,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    await service.update_manager(manager_id, payload)
    return {"message": "Manager updated"}

@router.patch("/managers/{manager_id}/disable")
async def disable_manager(
    manager_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    await service.disable_manager(manager_id)
    return {"message": "Manager disabled"}

@router.delete("/managers/{manager_id}")
async def delete_manager(
    manager_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    await service.delete_manager(manager_id)
    return {"message": "Manager deleted"}

# ========================
# USER OVERSIGHT
# ========================
@router.get("/users")
async def list_users(auth: AuthContext = Depends(get_current_user)):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    return await service.list_users()

@router.post("/users/{user_id}/delete-request")
async def request_user_deletion(
    user_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    await service.request_user_deletion(user_id, auth.user_id)
    return {"message": "Deletion requested"}

# ========================
# LOAN OVERSIGHT
# ========================
@router.get("/loans")
async def list_loans(auth: AuthContext = Depends(get_current_user)):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    return await service.list_loans()

@router.get("/loans/escalated")
async def escalated_loans(auth: AuthContext = Depends(get_current_user)):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    return await service.get_escalated_loans()

@router.post("/loans/{loan_id}/escalated-decision")
async def decide_escalated_loan(
    loan_id: str,
    payload: dict,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.ADMIN:
        raise HTTPException(403)
    await service.decide_escalated_loan(
        loan_id,
        payload["decision"],
        payload.get("reason"),
        auth.user_id
    )
    return {"message": "Decision recorded"}
