from datetime import datetime
from bson import ObjectId

from app.auth.password import hash_password
from app.enums.role import Role
from app.repositories.manager_repository import ManagerRepository
from app.repositories.user_repository import UserRepository
from app.repositories.loan_application_repository import LoanApplicationRepository
from app.repositories.audit_log_repository import AuditLogRepository


class AdminService:
    def __init__(self):
        self.manager_repo = ManagerRepository()
        self.user_repo = UserRepository()
        self.loan_repo = LoanApplicationRepository()
        self.audit_repo = AuditLogRepository()

    # ========================
    # MANAGER MANAGEMENT
    # ========================
    async def create_manager(self, payload):
        if payload.role not in [Role.BANK_MANAGER, Role.LOAN_MANAGER]:
            raise ValueError("Invalid manager role")

        existing = await self.manager_repo.find_by_manager_id(payload.manager_id)
        if existing:
            raise ValueError("Manager ID already exists")

        manager_doc = {
            "manager_id": payload.manager_id,
            "name": payload.name,
            "phone": payload.phone,
            "role": payload.role,
            "password_hash": hash_password(payload.password),
            "status": "ACTIVE",
            "approved_by_admin": True,
            "created_at": datetime.utcnow()
        }

        await self.manager_repo.create(manager_doc)

    async def list_managers(self):
        cursor = self.manager_repo.collection.find()
        managers = []

        async for manager in cursor:
            managers.append({
                "manager_id": manager.get("manager_id"),
                "name": manager.get("name"),
                "phone": manager.get("phone"),
                "role": manager.get("role"),
                "status": manager.get("status"),
                "created_at": manager.get("created_at")
            })

        return managers

    async def update_manager(self, manager_id: str, payload: dict):
        result = await self.manager_repo.collection.update_one(
            {"manager_id": manager_id},
            {"$set": payload}
        )
        if result.matched_count == 0:
            raise ValueError("Manager not found")

    async def disable_manager(self, manager_id: str):
        result = await self.manager_repo.collection.update_one(
            {"manager_id": manager_id},
            {"$set": {"status": "DISABLED", "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise ValueError("Manager not found")

    async def delete_manager(self, manager_id: str):
        result = await self.manager_repo.collection.delete_one(
            {"manager_id": manager_id}
        )
        if result.deleted_count == 0:
            raise ValueError("Manager not found")

    # ========================
    # USER OVERSIGHT
    # ========================
    async def list_users(self):
        cursor = self.user_repo.collection.find()
        users = []

        async for user in cursor:
            users.append({
                "user_id": str(user["_id"]),
                "name": user.get("name"),
                "phone": user.get("phone"),
                "kyc_status": user.get("kyc_status"),
                "approval_status": user.get("approval_status"),
                "created_at": user.get("created_at")
            })

        return users

    async def request_user_deletion(self, user_id: str, admin_id: str):
        result = await self.user_repo.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"delete_requested": True}}
        )
        if result.matched_count == 0:
            raise ValueError("User not found")

        await self.audit_repo.create({
            "actor_id": ObjectId(admin_id),
            "actor_role": "ADMIN",
            "action": "USER_DELETE_REQUESTED",
            "entity_type": "USER",
            "entity_id": ObjectId(user_id),
            "remarks": None,
            "timestamp": datetime.utcnow()
        })

    # ========================
    # LOAN OVERSIGHT
    # ========================
    async def list_loans(self):
        cursor = self.loan_repo.collection.find()
        loans = []

        async for loan in cursor:
            loan["_id"] = str(loan["_id"])
            loan["user_id"] = str(loan["user_id"])
            loans.append(loan)

        return loans

    async def get_escalated_loans(self):
        cursor = self.loan_repo.collection.find({"status": "ESCALATED"})
        loans = []

        async for loan in cursor:
            loan["_id"] = str(loan["_id"])
            loan["user_id"] = str(loan["user_id"])
            loans.append(loan)

        return loans

    async def decide_escalated_loan(
        self,
        loan_id: str,
        decision: str,
        reason: str | None,
        admin_id: str
    ):
        result = await self.loan_repo.collection.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    "status": decision,
                    "admin_decision_reason": reason,
                    "admin_decided_at": datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            raise ValueError("Loan not found")

        await self.audit_repo.create({
            "actor_id": ObjectId(admin_id),
            "actor_role": "ADMIN",
            "action": f"ESCALATED_LOAN_{decision}",
            "entity_type": "LOAN",
            "entity_id": ObjectId(loan_id),
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })
