from datetime import datetime
from bson import Decimal128
import logging

from app.repositories.loan_application_repository import LoanApplicationRepository
from app.repositories.user_repository import UserRepository
from app.enums.loan import LoanApplicationStatus
from app.enums.user import KYCStatus, UserApprovalStatus
from app.services.credit_rule_service import CreditRuleService

logger = logging.getLogger("loan_origination")

# ===============================
# CREDIT & FINANCIAL CALCULATIONS
# ===============================

def calculate_cibil(payload: dict) -> int:
    score = 300

    if payload["monthly_income"] * 12 >= payload["loan_amount"]:
        score += 180
    else:
        score += 90

    if payload["occupation"].lower() in ["employee", "government", "it"]:
        score += 120
    else:
        score += 60

    score += 120 if payload.get("previous_loans", 0) == 0 else 60
    score += 60 if payload.get("pending_emis", 0) == 0 else 20

    return min(score, 900)


# ===============================
# EMI CALCULATION
# ===============================
def calculate_emi(amount: float, rate: float, tenure: int) -> float:
    amount = float(amount)
    rate = float(rate)

    r = rate / (12 * 100)
    emi = (amount * r * ((1 + r) ** tenure)) / (((1 + r) ** tenure) - 1)

    return round(emi, 2)


# ===============================
# LOAN APPLICATION SERVICE
# ===============================
class LoanApplicationService:
    def __init__(self):
        self.repo = LoanApplicationRepository()
        self.user_repo = UserRepository()
        self.rule_service = CreditRuleService()

    # ----------------------------------
    # CREATE LOAN APPLICATION
    # ----------------------------------
    async def create_loan_application(
        self,
        user_id: str,
        payload,
        idempotency_key: str
    ):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # 🚦 Eligibility validation
        self._validate_user_eligibility(user)

        # 🔁 Idempotency check
        existing = await self.repo.find_by_idempotency_key(idempotency_key)
        if existing:
            return str(existing["_id"]), True

        # 🧠 Credit decision
        cibil = calculate_cibil(payload.dict())
        decision = await self.rule_service.evaluate_cibil(cibil)

        # 💰 Interest rate preview
        interest_rate = (
            8.5 if cibil >= 750 else
            11.5 if cibil >= 650 else
            14.0
        )

        # 💸 EMI preview (FIXED ORDER)
        emi_preview = calculate_emi(
            payload.loan_amount,
            interest_rate,
            payload.tenure_months
        )

        loan_doc = {
            "user_id": user["_id"],
            "loan_type": payload.loan_type,
            "loan_amount": Decimal128(str(payload.loan_amount)),
            "tenure_months": payload.tenure_months,
            "reason": payload.reason,
            "income_slip_url": str(payload.income_slip_url),

            "cibil_score": cibil,
            "system_decision": decision,

            "interest_rate": Decimal128(str(interest_rate)),
            "emi_preview": Decimal128(str(emi_preview)),

            "status": LoanApplicationStatus.PENDING,
            "applied_at": datetime.utcnow(),
            "idempotency_key": idempotency_key
        }

        loan_id = await self.repo.create(loan_doc)

        logger.info(
            "LOAN_APPLICATION_CREATED",
            extra={
                "loan_id": str(loan_id),
                "user_id": str(user["_id"]),
                "system_decision": decision
            }
        )

        return str(loan_id), False

    # ----------------------------------
    # GET LOAN APPLICATION (JSON SAFE)
    # ----------------------------------
    async def get_loan_application(self, loan_id: str):
        loan = await self.repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan application not found")

        return {
            "loan_id": str(loan["_id"]),
            "user_id": str(loan["user_id"]),
            "loan_type": loan.get("loan_type"),

            "loan_amount": str(loan.get("loan_amount"))
            if isinstance(loan.get("loan_amount"), Decimal128)
            else loan.get("loan_amount"),

            "tenure_months": loan.get("tenure_months"),
            "reason": loan.get("reason"),
            "income_slip_url": loan.get("income_slip_url"),

            "cibil_score": loan.get("cibil_score"),
            "system_decision": loan.get("system_decision"),
            "status": loan.get("status"),

            "interest_rate": str(loan.get("interest_rate"))
            if isinstance(loan.get("interest_rate"), Decimal128)
            else loan.get("interest_rate"),

            "emi_preview": str(loan.get("emi_preview"))
            if isinstance(loan.get("emi_preview"), Decimal128)
            else loan.get("emi_preview"),

            "applied_at": (
                loan.get("applied_at").isoformat()
                if loan.get("applied_at")
                else None
            )
        }

    # ----------------------------------
    # GET LOAN DECISION (READ ONLY)
    # ----------------------------------
    async def get_loan_decision(self, loan_id: str):
        loan = await self.repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan application not found")

        return {
            "loan_id": str(loan["_id"]),
            "user_id": str(loan["user_id"]),
            "system_decision": loan.get("system_decision"),
            "final_status": loan.get("status"),
            "decision_reason": loan.get("decision_reason"),
            "decided_at": (
                loan.get("decided_at").isoformat()
                if loan.get("decided_at")
                else None
            )
        }

    # ----------------------------------
    # ELIGIBILITY VALIDATION
    # ----------------------------------
    def _validate_user_eligibility(self, user: dict):
        if user["kyc_status"] != KYCStatus.COMPLETED:
            raise ValueError("KYC not completed")

        if user["approval_status"] != UserApprovalStatus.APPROVED:
            raise ValueError("User not approved by bank")

        if user.get("is_minor", False):
            raise ValueError("Minor users are not eligible for loans")
