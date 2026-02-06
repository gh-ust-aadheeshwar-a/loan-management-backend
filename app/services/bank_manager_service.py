from datetime import datetime
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.enums.user import KYCStatus, UserApprovalStatus
from app.schemas.user_decision import UserDecision
from app.repositories.loan_application_repository import LoanApplicationRepository
from app.schemas.user_delete import DeleteDecision




class BankManagerService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.loan_repo = LoanApplicationRepository()
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
    
    async def delete_user(self, manager_id: str, user_id: str, reason: str):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if user["approval_status"] == UserApprovalStatus.DELETED:
            raise ValueError("User already deleted")

        # 🛑 SAFETY CHECK — active loans
        active_loans = await self.loan_repo.count_active_loans(user_id)
        if active_loans > 0:
            raise ValueError("User has active loans")

        await self.user_repo.soft_delete_user(  
            user_id=user_id,
            deleted_by=manager_id
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "BANK_MANAGER",
            "action": "USER_DELETED",
            "entity_type": "USER",
            "entity_id": user_id,
            "remarks": reason
        })
    async def get_user_kyc_details(self, user_id: str):
        user = await self.user_repo.find_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        if user["kyc_status"] != KYCStatus.COMPLETED:
            raise ValueError("KYC not completed")

        if user["approval_status"] == UserApprovalStatus.DELETED:
            raise ValueError("User is deleted")

        return {
            "user_id": str(user["_id"]),
            "name": user["name"],
            "phone": user["phone"],
            "kyc": {
                "aadhaar": user.get("aadhaar"),
                "pan": user.get("pan"),
                "dob": user["dob"].isoformat() if user.get("dob") else None,
                "gender": user.get("gender"),
                "occupation": user.get("occupation"),
                "address": user.get("address")
            },
            "approval_status": user["approval_status"],
            "approved_by_manager_id": str(user.get("approved_by_manager_id"))
            if user.get("approved_by_manager_id") else None,
            "created_at": user["created_at"].isoformat()
        }
    
    async def handle_user_deletion_escalation(
        self,
        manager_id: str,
        user_id: str,
        decision: DeleteDecision,
        reason: str | None
    ):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not user.get("delete_requested", False):
            raise ValueError("No deletion request found for this user")

        if decision == DeleteDecision.APPROVE and not reason:
            raise ValueError("Reason is mandatory for deletion approval")

        if decision == DeleteDecision.APPROVE:
            active_loans = await self.loan_repo.count_active_loans(user_id)
            if active_loans > 0:
                raise ValueError("User has active loans")

            await self.user_repo.soft_delete_user(
                user_id=user_id,
                deleted_by=manager_id
            )

            await self.user_repo.collection.update_one(
                {"_id": user["_id"]},
                {"$unset": {"delete_requested": ""}}
            )

            action = "USER_DELETE_APPROVED"

        else:
            await self.user_repo.collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"delete_requested": False}}
            )

            action = "USER_DELETE_REJECTED"

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "BANK_MANAGER",
            "action": action,
            "entity_type": "USER",
            "entity_id": user_id,
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })

    