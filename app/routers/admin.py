from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import get_current_user, AuthContext
from app.enums.role import Role
from app.schemas.admin_manager import CreateManagerRequest, CreateManagerResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])
service = AdminService()


@router.post("/managers", response_model=CreateManagerResponse, status_code=201)
async def create_manager(
    payload: CreateManagerRequest,
    auth: AuthContext = Depends(get_current_user)
):
    if auth.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        await service.create_manager(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return CreateManagerResponse(
        manager_id=payload.manager_id,
        role=payload.role,
        message="Manager created successfully"
    )
