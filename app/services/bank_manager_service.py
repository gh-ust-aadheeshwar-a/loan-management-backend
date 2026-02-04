from datetime import datetime
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.enums.user import KYCStatus, UserApprovalStatus
from app.schemas.user_decision import UserDecision

class BankManagerService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.audit_repo = AuditLogRepository()

    async def decide_user(
        self,
        manager_id: str,
        user_id: str,
        decision: UserDecision,
        reason: str | None
    ):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if user["kyc_status"] != KYCStatus.COMPLETED:
            raise ValueError("KYC not completed")

        if user["approval_status"] != UserApprovalStatus.PENDING:
            raise ValueError("User already processed")

        if decision == UserDecision.REJECT and not reason:
            raise ValueError("Rejection reason is mandatory")

        approval_status = (
            UserApprovalStatus.APPROVED
            if decision == UserDecision.APPROVE
            else UserApprovalStatus.REJECTED
        )

        await self.user_repo.update_approval_status(
            user_id=user_id,
            approval_status=approval_status,
            approved_by_manager_id=manager_id
        )

        # 🧾 Audit log (BFS critical)
        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "BANK_MANAGER",
            "action": f"USER_{decision}",
            "entity_type": "USER",
            "entity_id": user_id,
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })
    async def list_users(self, approval_status=None, kyc_status=None):
        users_cursor = await self.user_repo.list_users(
            approval_status=approval_status,
            kyc_status=kyc_status
        )

        users = []
        async for user in users_cursor:
            users.append({
                "user_id": str(user["_id"]),
                "name": user["name"],
                "phone": user["phone"],
                "kyc_status": user["kyc_status"],
                "approval_status": user["approval_status"],
                "is_minor": user.get("is_minor", False),
                # masked Aadhaar if present
                "aadhaar": user.get("aadhaar"),
                "created_at": user["created_at"].isoformat()
            })

        return users
    
    async def get_user_details(self, user_id: str):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        return {
            "user_id": str(user["_id"]),
            "name": user["name"],
            "phone": user["phone"],

            "kyc_status": user["kyc_status"],
            "approval_status": user["approval_status"],
            "is_minor": user.get("is_minor", False),

            # KYC details (safe)
            "aadhaar": user.get("aadhaar"),  # already masked
            "pan": user.get("pan"),
            "dob": user["dob"].isoformat() if user.get("dob") else None,
            "gender": user.get("gender"),
            "occupation": user.get("occupation"),

            "address": user.get("address"),

            "created_at": user["created_at"].isoformat(),
            "updated_at": user.get("updated_at").isoformat()
            if user.get("updated_at") else None
        }
