from datetime import datetime
from bson import Decimal128
from app.repositories.loan_application_repository import LoanApplicationRepository
from app.enums.loan import LoanApplicationStatus
from app.enums.user import KYCStatus, UserApprovalStatus
from app.repositories.user_repository import UserRepository

class LoanApplicationService:
    def __init__(self):
        self.repo = LoanApplicationRepository()
        self.user_repo = UserRepository()

    async def create_loan_application(
        self,
        user_id: str,
        payload,
        idempotency_key: str
    ):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # 🚦 ELIGIBILITY CHECK
        await self._validate_user_eligibility(user)

        existing = await self.repo.find_by_idempotency_key(idempotency_key)
        if existing:
            return str(existing["_id"]), True

        loan_doc = {
            "user_id": user["_id"],
            "loan_type": payload.loan_type,
            "loan_amount": Decimal128(str(payload.loan_amount)),
            "tenure_months": payload.tenure_months,
            "reason": payload.reason,
            "income_slip_url": str(payload.income_slip_url),
            "status": LoanApplicationStatus.PENDING,
            "applied_at": datetime.utcnow(),
            "idempotency_key": idempotency_key
        }

        loan_id = await self.repo.create(loan_doc)
        return str(loan_id), False
    async def get_loan_application(self, loan_id: str):
        loan = await self.repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan application not found")

        # Convert ObjectId → str for response
        loan["loan_id"] = str(loan["_id"])
        loan["user_id"] = str(loan["user_id"])
        loan.pop("_id")

        # Convert Decimal128 if present
        if "loan_amount" in loan:
            loan["loan_amount"] = str(loan["loan_amount"])

        return loan
    
    async def _validate_user_eligibility(self, user: dict):
        if user["kyc_status"] != KYCStatus.COMPLETED:
            raise ValueError("KYC not completed")

        if user["approval_status"] != UserApprovalStatus.APPROVED:
            raise ValueError("User not approved by bank")

        if user.get("is_minor", False):
            raise ValueError("Minor users are not eligible for loans")
    