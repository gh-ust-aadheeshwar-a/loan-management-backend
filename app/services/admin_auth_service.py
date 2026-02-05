from app.repositories.admin_repository import AdminRepository
from app.auth.password import verify_password
from app.auth.security import create_access_token
from app.enums.role import Role

class AdminAuthService:
    def __init__(self):
        self.repo = AdminRepository()

    async def login_admin(self, username: str, password: str):
        # 🔍 DEBUG: incoming username
        print("\n===== ADMIN LOGIN DEBUG START =====")
        print("Login attempt username:", username)

        admin = await self.repo.find_by_username(username)

        if not admin:
            print("❌ Admin not found in database")
            print("===== ADMIN LOGIN DEBUG END =====\n")
            raise ValueError("Invalid credentials")

        # 🔍 DEBUG: admin record (SAFE FIELDS ONLY)
        print("✅ Admin found")
        print("Admin _id:", admin.get("_id"))
        print("Admin status:", admin.get("status"))

        password_match = verify_password(password, admin["password_hash"])
        print("Password match result:", password_match)

        if admin.get("status") != "ACTIVE":
            print("❌ Admin account is disabled")
            print("===== ADMIN LOGIN DEBUG END =====\n")
            raise ValueError("Admin account is disabled")

        if not password_match:
            print("❌ Password does NOT match")
            print("===== ADMIN LOGIN DEBUG END =====\n")
            raise ValueError("Invalid credentials")

        print("✅ Admin authenticated successfully")
        print("===== ADMIN LOGIN DEBUG END =====\n")

        return create_access_token(
            subject=str(admin["_id"]),
            role=Role.ADMIN
        )
