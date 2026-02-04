from app.repositories.manager_repository import ManagerRepository
from app.auth.password import verify_password
from app.auth.security import create_access_token
from app.enums.role import Role

class ManagerAuthService:
    def __init__(self):
        self.repo = ManagerRepository()

    async def login_manager(self, manager_id: str, password: str):
        manager = await self.repo.find_by_manager_id(manager_id)
        if not manager:
            raise ValueError("Invalid credentials")

        if manager["status"] != "ACTIVE":
            raise ValueError("Manager is disabled")

        if not manager.get("approved_by_admin", False):
            raise ValueError("Manager not approved by admin")

        if not verify_password(password, manager["password_hash"]):
            raise ValueError("Invalid credentials")

        return create_access_token(
            subject=str(manager["_id"]),
            role=manager["role"]  # BANK_MANAGER or LOAN_MANAGER
        )
