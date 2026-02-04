from datetime import datetime,time,date
from app.repositories.user_repository import UserRepository
from app.auth.password import hash_password
from app.enums.user import KYCStatus, UserApprovalStatus
from app.auth.password import verify_password
from app.auth.security import create_access_token
from app.enums.role import Role

class UserService:
    def __init__(self):
        self.repo = UserRepository()

    async def register_user(self, payload):
        existing = await self.repo.find_by_phone(payload.phone)
        if existing:
            raise ValueError("User already exists with this phone number")

        user_doc = {
            "name": payload.name,
            "phone": payload.phone,
            "password_hash": hash_password(payload.password),

            # KYC & approval lifecycle
            "kyc_status": KYCStatus.PENDING,
            "approval_status": UserApprovalStatus.PENDING,
            "is_minor": False,  # calculated during KYC

            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        user_id = await self.repo.create(user_doc)
        return str(user_id)
    
    async def login_user(self, phone: str, password: str):
        user = await self.repo.find_by_phone(phone)
        if not user:
            raise ValueError("Invalid phone or password")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid phone or password")

        token = create_access_token(
            subject=str(user["_id"]),
            role=Role.USER
        )

        return token
    
    async def get_user_by_id(self, user_id: str):
        user = await self.repo.find_by_id(user_id)
        if not user:
            return None

        # 🔐 Mask sensitive data
        return {
            "user_id": str(user["_id"]),
            "name": user["name"],
            "phone": user["phone"],
            "kyc_status": user["kyc_status"],
            "approval_status": user["approval_status"],
            "is_minor": user.get("is_minor", False),
            "created_at": user["created_at"].isoformat()
        }
    async def submit_kyc(self, user_id: str, payload):
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if user["kyc_status"] == KYCStatus.COMPLETED:
            raise ValueError("KYC already completed")

        # 🔞 Age check
        today = date.today()
        age = today.year - payload.dob.year - (
            (today.month, today.day) < (payload.dob.month, payload.dob.day)
        )
        is_minor = age < 18
        dob_datetime = datetime.combine(payload.dob, time.min)

        update_data = {
            "aadhaar": payload.aadhaar,
            "pan": payload.pan,
            "dob": dob_datetime,
            "gender": payload.gender,
            "occupation": payload.occupation,
            "address": payload.address.dict(),

            "is_minor": is_minor,
            "kyc_status": KYCStatus.COMPLETED,
            "updated_at": datetime.utcnow()
        }

        await self.repo.update_kyc(user_id, update_data)
