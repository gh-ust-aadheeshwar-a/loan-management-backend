from datetime import datetime
from app.repositories.loan_application_repository import LoanApplicationRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.cibil_service import CIBILService
from app.enums.loan import LoanApplicationStatus, SystemDecision
from app.schemas.loan_decision import LoanDecision
from bson import ObjectId, Decimal128
from app.repositories.loan_repository import LoanRepository
from app.services.loan_application_service import calculate_emi

class LoanManagerService:
    def __init__(self):
        self.loan_repo = LoanApplicationRepository()
        self.audit_repo = AuditLogRepository()
        self.user_repo = UserRepository()
        self.cibil_service = CIBILService()
        self.final_loan_repo = LoanRepository()

    # =====================================================
    # MANUAL DECISION (ONLY FOR MANUAL_REVIEW)
    # =====================================================
    async def decide_loan(
        self,
        loan_id: str,
        manager_id: str,
        decision: LoanDecision,
        reason: str | None
    ):
        loan = await self.loan_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan application not found")

        # 🔒 Enforce system decision rule
        if loan["system_decision"] != SystemDecision.MANUAL_REVIEW:
            raise ValueError(
                "Manual decision allowed only for MANUAL_REVIEW loans"
            )

        if loan["status"] not in [
            LoanApplicationStatus.PENDING,
            LoanApplicationStatus.MANUAL_REVIEW
        ]:
            raise ValueError("Loan already processed")

        if decision == LoanDecision.REJECT and not reason:
            raise ValueError("Rejection reason is mandatory")

        new_status = (
            LoanApplicationStatus.APPROVED
            if decision == LoanDecision.APPROVE
            else LoanApplicationStatus.REJECTED
        )

        await self.loan_repo.update_decision(
            loan_id=loan_id,
            status=new_status,
            decided_by=manager_id,
            reason=reason
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": f"LOAN_{decision}",
            "entity_type": "LOAN",
            "entity_id": loan_id,
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })

    # =====================================================
    # LIST LOANS (DASHBOARD)
    # =====================================================
    async def list_loans(self, system_decision=None):
        query = {}
        if system_decision:
            query["system_decision"] = system_decision

        cursor = self.loan_repo.collection.find(query)
        loans = []

        async for loan in cursor:
            loans.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": str(loan["loan_amount"]),
                "cibil_score": loan.get("cibil_score"),
                "system_decision": loan.get("system_decision"),
                "status": loan.get("status"),
                "escalated": loan.get("escalated", False)
            })

        return loans

    # =====================================================
    # AUTO APPROVED — CONFIRM ONLY
    # =====================================================
    async def confirm_auto_approved(self, loan_id: str, manager_id: str):
        loan = await self.loan_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.AUTO_APPROVED:
            raise ValueError("Loan is not auto-approved")

        await self.loan_repo.update_decision(
            loan_id=loan_id,
            status=LoanApplicationStatus.APPROVED,
            decided_by=manager_id,
            reason=None
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": "LOAN_AUTO_APPROVED_CONFIRMED",
            "entity_type": "LOAN",
            "entity_id": loan_id,
            "remarks": None,
            "timestamp": datetime.utcnow()
        })

    # =====================================================
    # AUTO REJECTED — SYSTEM FINAL
    # =====================================================
    async def confirm_auto_rejected(self, loan_id: str, manager_id: str):
        loan = await self.loan_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.AUTO_REJECTED:
            raise ValueError("Loan not auto-rejected")

        await self.loan_repo.update_decision(
            loan_id=loan_id,
            status=LoanApplicationStatus.REJECTED,
            decided_by=manager_id,
            reason="Auto rejected by system"
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": "LOAN_AUTO_REJECTED",
            "entity_type": "LOAN",
            "entity_id": loan_id,
            "remarks": "Auto rejected by system",
            "timestamp": datetime.utcnow()
        })

    # =====================================================
    # ESCALATE TO ADMIN (MANUAL_REVIEW ONLY)
    # =====================================================
    async def escalate_to_admin(self, loan_id: str, reason: str, manager_id: str):
        loan = await self.loan_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.MANUAL_REVIEW:
            raise ValueError("Only MANUAL_REVIEW loans can be escalated")

        await self.loan_repo.collection.update_one(
            {"_id": loan["_id"]},
            {
                "$set": {
                    "status": LoanApplicationStatus.ESCALATED,
                    "escalated": True,
                    "escalated_reason": reason,
                    "escalated_at": datetime.utcnow()
                }
            }
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": "LOAN_ESCALATED",
            "entity_type": "LOAN",
            "entity_id": loan["_id"],
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })

    # =====================================================
    # LOAN CLOSURE → CIBIL UPDATE (EVENT-BASED)
    # =====================================================
    async def close_loan(self, loan_id: str, manager_id: str):
        loan = await self.loan_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan["status"] != LoanApplicationStatus.APPROVED:
            raise ValueError("Only active loans can be closed")

        # ✅ Close loan
        await self.loan_repo.collection.update_one(
            {"_id": loan["_id"]},
            {
                "$set": {
                    "status": LoanApplicationStatus.CLOSED,
                    "closed_at": datetime.utcnow()
                }
            }
        )

        # 🧠 EVENT-BASED CIBIL CALCULATION
        cibil_score = self.cibil_service.calculate({
            "missed_emis": loan.get("missed_emis", 0),
            "late_payments": loan.get("late_payments", 0),
            "loan_closed_clean": True
        })

        await self.user_repo.collection.update_one(
            {"_id": loan["user_id"]},
            {
                "$set": {
                    "cibil_score": cibil_score,
                    "cibil_updated_at": datetime.utcnow()
                }
            }
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": "LOAN_CLOSED",
            "entity_type": "LOAN",
            "entity_id": loan_id,
            "remarks": f"CIBIL updated to {cibil_score}",
            "timestamp": datetime.utcnow()
        })

    async def list_escalated_loans(self):
        cursor = await self.loan_repo.find_escalated_loans()
        loans = []
        async for loan in cursor:
            loans.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": str(loan["loan_amount"]),
                "cibil_score": loan.get("cibil_score"),
                "system_decision": loan.get("system_decision"),
                "status": loan.get("status"),
                "escalated_reason": loan.get("escalated_reason"),
                "applied_at": loan.get("applied_at")
            })

        return loans
    async def list_loans_ready_for_finalization(self):
        cursor = self.loan_repo.collection.find({
            "status": "ADMIN_APPROVED"
        })

        loans = []
        async for loan in cursor:
            loans.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": str(loan["loan_amount"]),
                "cibil_score": loan.get("cibil_score"),
                "system_decision": loan.get("system_decision"),
                "admin_decision": loan.get("admin_decision"),
                "admin_decision_reason": loan.get("admin_decision_reason"),
                "status": loan["status"]
            })
        return loans

    async def finalize_loan(
    self,
    loan_id: str,
    manager_id: str,
    interest_rate: float,
    tenure_months: int
):
        loan_app = await self.loan_repo.find_by_id(loan_id)
        if not loan_app:
            raise ValueError("Loan application not found")

        if loan_app["status"] != "ADMIN_APPROVED":
            raise ValueError(
                "Loan can be finalized only after admin approval"
        )


        emi = calculate_emi(
            float(loan_app["loan_amount"]),
            tenure_months,
            interest_rate
        )

        loan_doc = {
            "loan_application_id": loan_app["_id"],
            "user_id": loan_app["user_id"],
            "approved_by": ObjectId(manager_id),
            "approved_role": "LOAN_MANAGER",
            "principal_amount": loan_app["loan_amount"],
            "interest_rate": Decimal128(str(interest_rate)),
            "tenure_months": tenure_months,
            "emi_amount": Decimal128(str(emi)),
            "loan_status": "ACTIVE",
            "disbursed_at": None,
            "closed_at": None,
            "created_at": datetime.utcnow()
        }

        await self.final_loan_repo.create(loan_doc)

        await self.loan_repo.collection.update_one(
            {"_id": loan_app["_id"]},
            {"$set": {"status": "FINALIZED"}}
        )

        await self.audit_repo.create({
            "actor_id": ObjectId(manager_id),
            "actor_role": "LOAN_MANAGER",
            "action": "LOAN_FINALIZED",
            "entity_type": "LOAN",
            "entity_id": loan_app["_id"],
            "remarks": None,
            "timestamp": datetime.utcnow()
        })

