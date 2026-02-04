from datetime import datetime
from app.repositories.manager_repository import ManagerRepository
from app.auth.password import hash_password
from app.enums.role import Role

class AdminService:
    def __init__(self):
        self.manager_repo = ManagerRepository()

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
