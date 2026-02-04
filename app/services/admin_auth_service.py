from app.repositories.admin_repository import AdminRepository
from app.auth.password import verify_password
from app.auth.security import create_access_token
from app.enums.role import Role

class AdminAuthService:
    def __init__(self):
        self.repo = AdminRepository()

    async def login_admin(self, username: str, password: str):
        admin = await self.repo.find_by_username(username)
        if not admin:
            raise ValueError("Invalid credentials")

        if admin.get("status") != "ACTIVE":
            raise ValueError("Admin account is disabled")

        if not verify_password(password, admin["password_hash"]):
            raise ValueError("Invalid credentials")

        return create_access_token(
            subject=str(admin["_id"]),
            role=Role.ADMIN
        )
